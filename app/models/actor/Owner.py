from .Role import Role
from app import db
from .User import User

    
class Owner(User):
    __tablename__ = 'owner'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'owner',
    }
    # Constructor to ensure the role is set to OWNER for all Owner instances
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.role = Role.OWNER