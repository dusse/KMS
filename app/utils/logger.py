import os
import logging
from logging.handlers import RotatingFileHandler

from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
from flask import has_request_context, request


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            if request.headers.getlist("X-Forwarded-For"):
                record.remote_addr = request.headers.getlist("X-Forwarded-For")[0]
            else:
                record.remote_addr = request.remote_addr
        else:
            record.url = "no-url"
            record.remote_addr = "no-remote-addr"
        return super(RequestFormatter, self).format(record)


def setup_logging(app, basedir):
    log_dir = os.path.join(basedir, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    if not app.debug:
        # Set up logging to file
        file_handler = RotatingFileHandler(os.path.join(basedir, 'logs', 'app.log'), 
                                           maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(RelativePathFormatter(
             '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        if app.config['DEBUG_MODE']:
            file_handler.setLevel(logging.DEBUG)
        else:
            file_handler.setLevel(logging.INFO)

        app.logger.addHandler(file_handler)
        if app.config['DEBUG_MODE']:
            app.logger.setLevel(logging.DEBUG)
        else:
            app.logger.setLevel(logging.INFO)
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
            app.logger.debug("Start Query: %s", statement)

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - conn.info['query_start_time'].pop(-1)
            app.logger.debug("Query Complete: %s", statement)
            app.logger.debug("Query Time: %.02fms", total * 1000)

def initConsoleHandler(app):
    # Console Handler for Server Logs
    console_handler = logging.StreamHandler()
    if app.config['DEBUG_MODE']:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
    
    console_handler.setFormatter(RequestFormatter(
        '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
        '%(levelname)s in %(module)s: %(message)s'
    ))

class RelativePathFormatter(logging.Formatter):
    def format(self, record):
        # Set the base directory for relative path calculation
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Convert the absolute pathname to a relative pathname
        record.pathname = os.path.relpath(record.pathname, base_dir)
        
        return super(RelativePathFormatter, self).format(record)

def initUserBehaviorLogger(app, basedir):
    # Set up logging for user behavior
    user_behavior_handler = RotatingFileHandler(os.path.join(basedir, 'logs', 'user_behavior.log'), 
                                                maxBytes=10240000, backupCount=20)
    user_behavior_handler.setFormatter(RelativePathFormatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    user_behavior_handler.setLevel(logging.INFO)
    user_behavior_logger = logging.getLogger('user_behavior')
    user_behavior_logger.setLevel(logging.INFO)
    user_behavior_logger.addHandler(user_behavior_handler)
    
    return user_behavior_logger
