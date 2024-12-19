from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
from .Role import Role


    
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.Enum(Role), default=Role.WORKER, nullable=False)
    first_login = db.Column(db.Boolean, default=True)
    comment = db.Column(db.String(255), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    createdby_id = db.Column(db.Integer, unique=False, nullable=False, default=-1)
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity':'user',
        'polymorphic_on':type
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def reset_password(self, new_password):
        self.set_password(new_password)
        self.first_login = True
        db.session.commit()