from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .jinja_component import AddButton, TableActionButtons, SearchForm, Modal, Pagination
from .jinja_component import DynamicCard, DynamicTable, HeaderComponent, SelectorModal

from app.utils.logger import setup_logging, initConsoleHandler

import configparser
from datetime import timedelta

import os

db = SQLAlchemy()
login_manager = LoginManager()

LOGIN_URL = 'auth.login'


def create_app():
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    
    app = Flask(__name__, static_folder=os.path.join(basedir, 'static'))
    
    config = configparser.ConfigParser()
    config.read(os.path.join(basedir, 'app.config.ini'))

    app.config['BASEDIR'] = basedir
    app.config['LOGINURL'] = LOGIN_URL
    app.config['IMGS_PATH'] = "static/imgs"    

    app.config['DEBUG_MODE']=config.getboolean('General', 'DEBUG_MODE')

    app.config['UPLOAD_FOLDER'] = config['General']['UPLOAD_FOLDER']
    app.config['BIBLIO_UPLOAD_FOLDER'] = config['General']['BIBLIO_UPLOAD_FOLDER']    

    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

    if app.config['DEBUG_MODE']:
        app.config['SECRET_KEY'] = 'key_for_test'
    else:
        app.config['SECRET_KEY'] = config['General']['SECRET_KEY']

    db_username = config['Database']['DB_USERNAME']
    db_password = config['Database']['DB_PASSWORD']
    db_host = config['Database']['DB_HOST']
    db_name = config['Database']['DB_NAME']
    db_port = config['Database']['DB_PORT']

    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.getboolean('Database', 'SQLALCHEMY_TRACK_MODIFICATIONS')

    db.init_app(app)
    
    setup_logging(app, basedir)
    initConsoleHandler(app)

    login_manager.init_app(app)
    login_manager.login_view = LOGIN_URL
    
    from app.routes.auth import auth
    from app.routes.owner import owner
    from app.routes.worker import worker
    from app.routes import misc
    from app.routes.crud import users, generic, knowledges, knownitem, biblio
    from app.utils.utils import replace_cite
    
    app.register_blueprint(generic.bp, url_prefix='/api')

    app.register_blueprint(auth.bp, url_prefix='/auth')
    app.register_blueprint(owner.bp)
    app.register_blueprint(worker.bp)
    app.register_blueprint(users.bp)
    
    app.register_blueprint(knowledges.bp, url_prefix='/api/knowledge/')
    app.register_blueprint(biblio.bp, url_prefix='/api/biblio/')
    app.register_blueprint(knownitem.bp, url_prefix='/api/knownitem/')    

    app.register_blueprint(misc.bp)

    app.jinja_env.globals.update(AddButton=AddButton)
    app.jinja_env.globals.update(TableActionButtons=TableActionButtons)
    app.jinja_env.globals.update(SearchForm=SearchForm)
    app.jinja_env.globals.update(Modal=Modal)
    app.jinja_env.globals.update(Pagination=Pagination)
    app.jinja_env.globals.update(DynamicTable=DynamicTable)
    app.jinja_env.globals.update(DynamicCard=DynamicCard)
    app.jinja_env.globals.update(HeaderComponent=HeaderComponent)
    app.jinja_env.globals.update(SelectorModal=SelectorModal)

    app.jinja_env.globals.update(replace_cite=replace_cite)

    return app
