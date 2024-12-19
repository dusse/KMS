from flask import Blueprint, render_template, request, jsonify
from flask import redirect, url_for, flash, send_file, current_app
from flask_login import  login_required, current_user
from sqlalchemy import cast, String

from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.sql.expression import desc

from app.models import User, Role
import os
from app import db
from app.decorators import role_required
from app.models import ProgressStatus, SharingStatus
from app.models import Theme, KnownItem, KnowledgeType, Knowledge, Log, Biblio

bp = Blueprint('ownerflow', __name__)

MAIN_URL = 'ownerflow.owner_space'

@bp.route('/owner_space')
@login_required
@role_required(Role.OWNER)
def owner_space():
    return render_template('owner/space.html')


class Option:
    def __init__(self, id, name):
        self.id = id
        self.name = name


def get_status_options(enum_class):
    return [Option(status.tagname, status.description) for status in enum_class]

available_progress_statuses = get_status_options(ProgressStatus)
available_sharing_statuses = get_status_options(SharingStatus)


@bp.route('/item/complex_tab/<int:knowledge_id>')
@login_required
@role_required(Role.OWNER, Role.WORKER)
def complex_tab(knowledge_id):
    # Retrieve the knowledge item and its associated items
    knowledge =  Knowledge.query.get_or_404(knowledge_id)

    if not knowledge:
        return jsonify({'error': 'Knowledge not found'}), 404

    knowledgetypes = KnowledgeType.query.all()

    return render_template('knowledge/item/complex_tab.html', 
                           knowledge=knowledge, 
                           knowledgetypes=knowledgetypes,
                           available_progress_statuses=available_progress_statuses,
                           ProgressStatus=ProgressStatus) 
    

@bp.route('/get_owner_tab_content')
@login_required
@role_required(Role.OWNER)
def get_owner_tab_content():

    tab_name = request.args.get('tab')
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    search_field = request.args.get('field', '')
    max_items_per_page = 12

    if tab_name == 'coworkers':
        query = User.query.filter(User.role == Role.WORKER)
        query = query.order_by(User.id.desc())
        if search:
            query = query.filter(User.name.ilike(f'%{search}%'))
        workers = query.paginate(page=page, per_page=max_items_per_page)
        return render_template('owner/actors/worker_tab.html', items=workers)

    elif tab_name == 'themes':
        query = Theme.query.order_by(Theme.id.desc())
        if search:
            query = query.filter(Theme.name.ilike(f'%{search}%'))
        papers = query.paginate(page=page, per_page=max_items_per_page)

        return render_template('owner/prefs/themes_tab.html', items=papers)

    elif tab_name == 'biblio':
        query = Biblio.query.order_by(Biblio.id.desc())
        if search:
            query = query.filter(Biblio.name.ilike(f'%{search}%'))
        biblios = query.paginate(page=page, per_page=max_items_per_page)

        return render_template('owner/prefs/biblio_tab.html', items=biblios)

    elif tab_name == 'knowledges':
        query = Knowledge.query
        query = query.filter(or_(Knowledge.sharing_status == SharingStatus.shared, Knowledge.creator_name == current_user.name))    
        query = query.order_by(Knowledge.id.desc())
        if search:
            query = query.filter(cast(Knowledge.unique_number, String).ilike(f'%{search}%'))
        knowledges = query.paginate(page=page, per_page=max_items_per_page)
        knowledgetypes = KnowledgeType.query.all()

        active_themes = Theme.query.filter_by(is_active=True).all()

        return render_template('knowledge/complex_tab.html', 
                               items=knowledges,
                               knowledgetypes=knowledgetypes,
                               themes=active_themes,
                               available_progress_statuses=available_progress_statuses,
                               available_sharing_statuses=available_sharing_statuses)

    elif tab_name == 'knowledgetypes':
        query = KnowledgeType.query
        query = query.order_by(KnowledgeType.id.desc())
        if search:
            query = query.filter(cast(KnowledgeType.name, String).ilike(f'%{search}%'))
        knowledgetypes = query.paginate(page=page, per_page=max_items_per_page)

        return render_template('owner/prefs/knowledgetypes_tab.html', 
                               items=knowledgetypes)
        
    elif tab_name == 'logs':
        query = Log.query.order_by(Log.id.desc())
        if search:
            query = query.filter(Log.message.ilike(f'%{search}%'))
        logs = query.paginate(page=page, per_page=max_items_per_page)
        return render_template('owner/logs_tab.html', items=logs)


    return redirect(url_for(current_app.config['LOGINURL']))


