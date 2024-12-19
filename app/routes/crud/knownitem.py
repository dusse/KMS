from flask import Blueprint, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from app.decorators import role_required
from app.models import User, Role, KnownItem, KnownItemVersion, Biblio, Log
from datetime import datetime

from app import db

bp = Blueprint('knownitem', __name__)

@bp.route('/deleteVer/<int:version_id>', methods=['DELETE'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def delete_version(version_id):

    version = KnownItemVersion.query.get(version_id)
    if not version:
        return jsonify({'error': 'Version not found'}), 404
    try:
        db.session.delete(version)
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error deleting version: {str(e)}'}), 500



@bp.route('/<int:item_id>/history', methods=['GET'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def get_item_history(item_id):
    known_item = KnownItem.query.get(item_id)
    
    if not known_item:
        return jsonify({'error': 'KnownItem not found'}), 404

    previous_versions = []

    versions = KnownItemVersion.query.filter_by(known_item_id=item_id).order_by(KnownItemVersion.modified_at.desc()).all()

    for version in versions:
        previous_versions.append({
            'versionName': f"Version {version.version_number}",
            'id': version.id,
            'name': version.name,
            'description': version.description,
            'content': version.content
        })

    return jsonify({
        'id': known_item.id,
        'name': known_item.name,
        'description': known_item.description,
        'content': known_item.content,    
        'previousVersions': previous_versions
    })


@bp.route('/update/<int:obj_id>/', methods=['PUT'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def update_known_item(obj_id):
    # Fetch the KnownItem object by its ID
    known_item = KnownItem.query.get(obj_id)

    if not known_item:
        return jsonify({'error': 'KnownItem not found'}), 404

    # Get the updated data from the request
    data = request.get_json()

    description_changed = data.get('description', known_item.description) != known_item.description
    content_changed = data.get('content', known_item.content) != known_item.content

    if description_changed or content_changed:
        known_item.create_new_version(current_user.name)

    known_item.name = data.get('name', known_item.name)
    known_item.progress_status = data.get('progress_status', known_item.progress_status)
    known_item.description = data.get('description', known_item.description)
    known_item.content = data.get('content', known_item.content)

    message = (
        f"[{current_user.name}] updated item {known_item.name} of the knowledge "
        f"<a href='#' onclick=\"loadTabContent('knowledges', 1, '{known_item.knowledge.unique_number}', '');\">"
        f"'{known_item.knowledge.unique_number}'</a>"
    )
    log_entry = Log(
        message=message,
        date=datetime.utcnow()
    )

    db.session.add(log_entry)

    db.session.commit()

    return jsonify({'id': known_item.id}), 200

@bp.route('/addBibliography', methods=['POST'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def add_bibliography():
    data = request.get_json()
    known_item_id = data.get('knownItemId')
    bibliography_id = data.get('bibliographyId')

    # Debugging: the received data
    current_app.logger.debug(f"Received data: KnownItemId = {known_item_id}, BibliographyId = {bibliography_id}")

    # Find the KnownItem
    known_item = KnownItem.query.get(known_item_id)
    if not known_item:
        current_app.logger.error(f"KnownItem with ID {known_item_id} not found")
        return jsonify({'error': 'KnownItem not found'}), 404

    # Debugging: the current bibliography_ids before modification
    current_app.logger.debug(f"Current bibliography_ids for KnownItem {known_item_id}: {known_item.bibliography_ids}")

    # Check if bibliography_ids is None, and initialize it to an empty list if necessary
    if known_item.bibliography_ids is None:
        current_app.logger.error(f"Bibliography IDs for KnownItem {known_item_id} is None, initializing it to an empty list.")
        known_item.bibliography_ids = []

    # Find the Bibliography
    bibliography = Biblio.query.get(bibliography_id)
    if not bibliography:
        current_app.logger.error(f"Bibliography with ID {bibliography_id} not found")        
        return jsonify({'error': 'Bibliography not found'}), 404

    # Add the bibliography to the KnownItem
    if bibliography_id not in known_item.bibliography_ids:
        current_app.logger.debug(f"Adding Bibliography with ID {bibliography_id} to KnownItem {known_item_id}")
        known_item.bibliography_ids.append(bibliography_id)

        # Commit the changes
        db.session.flush()
        db.session.commit()
        db.session.refresh(known_item)
        # Debugging: Check if the change was committed
        current_app.logger.debug(f"Bibliography with ID {bibliography_id} added to KnownItem {known_item_id}")
        current_app.logger.debug(f"New bibliography_ids for KnownItem {known_item_id}: {known_item.bibliography_ids}")
        
        return jsonify({'success': True}), 200
    else:
        current_app.logger.error(f"Bibliography with ID {bibliography_id} already added to KnownItem {known_item_id}")
        return jsonify({'error': 'Bibliography already added'}), 400




@bp.route('/biblio', methods=['GET'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def get_all_bibliographies():
    # Fetch all bibliographies from the database
    bibliographies = Biblio.query.all()

    # Create a list of bibliographies with year and title
    bibliography_list = [{
        'id': biblio.id,
        'name': biblio.name,
        'title': biblio.title
    } for biblio in bibliographies]

    return jsonify({'bibliographies': bibliography_list}), 200


@bp.route('/<int:known_item_id>/biblio', methods=['GET'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def get_bibliographies_for_known_item(known_item_id):
    # Find the KnownItem by ID
    known_item = KnownItem.query.get(known_item_id)
    if not known_item:
        return jsonify({'error': 'KnownItem not found'}), 404

    # Ensure bibliography_ids is not None
    bibliography_ids = known_item.bibliography_ids or []

    # Fetch all bibliographies that are associated with this KnownItem
    bibliographies = Biblio.query.filter(Biblio.id.in_(bibliography_ids)).all()

    # Create a list of bibliographies with year and title
    bibliography_list = [{
        'id': biblio.id,
        'name': biblio.name,
        'title': biblio.title
    } for biblio in bibliographies]

    return jsonify({'bibliographies': bibliography_list}), 200



@bp.route('/removeBibliography', methods=['POST'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def remove_bibliography():
    data = request.get_json()
    known_item_id = data.get('knownItemId')
    bibliography_id = data.get('bibliographyId')

    # Debugging: the received data
    current_app.logger.debug(f"Received data: KnownItemId = {known_item_id}, BibliographyId = {bibliography_id}")

    # Find the KnownItem by ID
    known_item = KnownItem.query.get(known_item_id)
    if not known_item:
        current_app.logger.error(f"KnownItem with ID {known_item_id} not found")
        return jsonify({'error': 'KnownItem not found'}), 404

    # Check if bibliography_ids is None, and initialize it to an empty list if necessary
    if known_item.bibliography_ids is None:
        current_app.logger.error(f"Bibliography IDs for KnownItem {known_item_id} is None, initializing it to an empty list.")
        known_item.bibliography_ids = []

    # Convert bibliography_id to string if it's not a string already
    bibliography_id_str = str(bibliography_id)

    # Check if bibliography_id is in the bibliography_ids list and remove it
    if bibliography_id_str in known_item.bibliography_ids:
        current_app.logger.debug(f"Removing Bibliography with ID {bibliography_id_str} from KnownItem {known_item_id}")

        known_item.bibliography_ids.remove(bibliography_id_str)  # Remove the bibliography_id
        db.session.commit()
        current_app.logger.debug(f"Bibliography with ID {bibliography_id_str} removed from KnownItem {known_item_id}")
        return jsonify({'success': True}), 200
    else:
        current_app.logger.error(f"Bibliography with ID {bibliography_id_str} not found in KnownItem {known_item_id}")
        return jsonify({'error': 'Bibliography not found in KnownItem'}), 404


