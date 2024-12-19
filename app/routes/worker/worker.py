from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file, current_app
from flask_login import  login_required, current_user
from sqlalchemy import cast, String

from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy.sql.expression import desc

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from app.models import User, Role, ProgressStatus, SharingStatus
from app.models import KnowledgeType, Knowledge, Theme
from app.decorators import role_required

from datetime import datetime
from sqlalchemy import or_
import os
from app import db

import uuid

bp = Blueprint('workerflow', __name__)

MAIN_URL = 'workerflow.worker_space'

@bp.route('/worker_space')
@login_required
@role_required(Role.WORKER)
def worker_space():
    return render_template('worker/space.html')


class Option:
    def __init__(self, id, name):
        self.id = id
        self.name = name


def get_status_options(enum_class):
    return [Option(status.tagname, status.description) for status in enum_class]

available_progress_statuses = get_status_options(ProgressStatus)
available_sharing_statuses = get_status_options(SharingStatus)

@bp.route('/get_worker_tab_content')
@login_required
@role_required(Role.WORKER)
def get_worker_tab_content():

    tab_name = request.args.get('tab')
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    search_field = request.args.get('field', '')
    max_items_per_page = 12

    if tab_name == 'knowledges':
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
        


    return redirect(url_for(current_app.config['LOGINURL']))



