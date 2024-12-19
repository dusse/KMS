from app import create_app, db
from sqlalchemy.exc import IntegrityError
from flask import current_app
from app.utils.utils import add_owner, init_db

app = create_app()

STATIC_FOLDER = app.static_folder

with app.app_context():
    try:
        init_db()
        add_owner()
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"IntegrityError: {e}")

if __name__ == '__main__':
    app.run()