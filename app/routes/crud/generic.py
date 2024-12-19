from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import  login_required
from app.models import Knowledge, KnownItem, KnowledgeType, Theme, Role, Biblio
from app.models.crud_base import CRUDBase
from app.decorators import role_required
import pandas as pd

bp = Blueprint('crud', __name__)

# Define CRUD instances for each model
crud_theme = CRUDBase(Theme)
crud_biblio = CRUDBase(Biblio)
crud_knowledgetype = CRUDBase(KnowledgeType)
crud_knowledge = CRUDBase(Knowledge)
crud_knownitem = CRUDBase(KnownItem)

model_map = {
    'theme': crud_theme,
    'biblio': crud_biblio,
    'knowledge': crud_knowledge,
    'knowledgetype': crud_knowledgetype,
    'knownitem': crud_knownitem
}

# Function to get CRUD instance based on model name
def get_crud_for_model(model_name):
    return model_map.get(model_name)


# Generalized routes for downloading and uploading Excel files
@bp.route('/<model_name>/download_excel', methods=['GET'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def download_excel(model_name):
    """
    Download Excel file for the specified model.
    """
    crud_instance = model_map.get(model_name.lower())
    
    if crud_instance is None:
        return jsonify({'error': 'Invalid model name'}), 400

    output = crud_instance.create_excel_from_records()

    if isinstance(output, tuple):
        return output  # Handle errors gracefully

    return send_file(output, as_attachment=True, download_name=f"{model_name}.xlsx")


@bp.route('/<model_name>/upload_excel', methods=['POST'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def upload_excel(model_name):
    """
    Upload Excel file for the specified model.
    """
    crud_instance = model_map.get(model_name.lower())
    
    if crud_instance is None:
        return jsonify({'error': 'Invalid model name'}), 400

    excel_file = request.files.get('excel_file')
    current_app.logger.debug("upload_excel, model_name = ", model_name)

    if not excel_file:
        return jsonify({'error': 'No file uploaded.'}), 400

    try:
        # Attempt to read the Excel file
        df = pd.read_excel(excel_file)
        data = df.to_dict(orient='records')  # Convert DataFrame to a list of dicts
        current_app.logger.debug(f"Parsed data: {data}")
        crud_instance.process_records_from_excel(data)  # Process and insert the data into the database
        return jsonify({'message': 'Data successfully uploaded.'}), 200
    except ValueError as ve:
        current_app.logger.error(f"ValueError occurred: {str(ve)}")
        return jsonify({'error': str(ve)}), 400  # Handle validation errors specifically
    except Exception as e:
        current_app.logger.error(f"Error occurred: {str(ve)}")
        return jsonify({'error': str(e)}), 400  # Handle other exceptions


@bp.route('/<model_name>/<int:obj_id>', methods=['GET'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def get_model_by_id(model_name, obj_id):
    # Get the CRUD instance for the specified model
    crud = get_crud_for_model(model_name)
    if not crud:
        current_app.logger.error(f'Invalid model name {model_name}')
        return jsonify({'error': 'Invalid model name'}), 400

    # Fetch the specific object by ID
    item = crud.get(obj_id)
    if not item:
        return jsonify({'error': f'{model_name} with ID {obj_id} not found.'}), 404

    return jsonify(item.to_dict())


# Add pagination to GET requests
@bp.route('/<model_name>', methods=['GET'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def get_models(model_name):
    crud = get_crud_for_model(model_name)
    if not crud:
        current_app.logger.error(f'Invalid model name {model_name}')
        return jsonify({'error': 'Invalid model name'}), 400

    # Fetch pagination parameters from the query string
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get paginated results from the CRUD instance
    paginated_items = crud.get_all_paginated(page, per_page)

    return jsonify({
        'items': [item.to_dict() for item in paginated_items.items],
        'total': paginated_items.total,
        'page': paginated_items.page,
        'pages': paginated_items.pages,
        'has_prev': paginated_items.has_prev,
        'has_next': paginated_items.has_next,
        'prev_num': paginated_items.prev_num,
        'next_num': paginated_items.next_num,
    })


@bp.route('/<model_name>', methods=['POST'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def create_model(model_name):
    crud = get_crud_for_model(model_name)
    if not crud:
        current_app.logger.error(f'Invalid model name {model_name}')
        return jsonify({'error': 'Invalid model name'}), 400
    
    data = request.get_json()
    current_app.logger.debug(f"Received data: {data}")
    try:
        new_object = crud.create(data)
        current_app.logger.debug(f"Created new object with ID: {new_object.id}")
        return jsonify({'id': new_object.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400



@bp.route('/<model_name>/<int:obj_id>', methods=['PUT'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def update_model(model_name, obj_id):
    crud = get_crud_for_model(model_name)
    if not crud:
        current_app.logger.error(f'Invalid model name {model_name}')
        return jsonify({'error': 'Invalid model name'}), 400
    
    data = request.get_json()
    updated_object = crud.update(obj_id, data)
    if updated_object:
        return jsonify({'id': updated_object.id}), 200
    return jsonify({'error': 'Object not found'}), 404


@bp.route('/<model_name>/<int:obj_id>', methods=['DELETE'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def delete_model(model_name, obj_id):
    crud = get_crud_for_model(model_name)
    if not crud:
        current_app.logger.error(f'Invalid model name {model_name}')
        return jsonify({'error': 'Invalid model name'}), 400
    deleted_object = crud.delete(obj_id)
    if deleted_object:
        return jsonify({'message': 'Object deleted'}), 200
    return jsonify({'error': 'Object not found'}), 404


@bp.route('/<model_name>/toggle/<int:obj_id>', methods=['PATCH'])
@login_required
@role_required(Role.OWNER, Role.WORKER)
def toggle_status(model_name, obj_id):
    crud = get_crud_for_model(model_name)
    if not crud:
        current_app.logger.error(f'Invalid model name {model_name}')
        return jsonify({'error': 'Invalid model name'}), 400
    
    data = request.get_json()
    is_active = data.get('is_active', False)
    
    item = crud.get(obj_id)
    if item:
        item.is_active = is_active
        crud.update(obj_id, {'is_active': is_active})
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Item not found.'}), 404

