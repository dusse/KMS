from app import db
from .SharingStatus import SharingStatus
from sqlalchemy import event

class Knowledge(db.Model):
    __tablename__ = 'knowledges'
    
    id = db.Column(db.Integer, primary_key=True)
    unique_number = db.Column(db.Integer, unique=True, nullable=False, 
                default=db.Sequence('knowledge_unique_number_seq', start=1000001, increment=2))
    
    creator_name = db.Column(db.String(50), nullable=False)

    theme_name = db.Column(db.String(100), nullable=False)

    known_items = db.relationship('KnownItem', back_populates='knowledge', cascade="all, delete-orphan")

    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(100), nullable=True)

    sharing_status = db .Column(db.Enum(SharingStatus), default=SharingStatus.private, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f"<Knowledge(name={self.name}, creator_name={self.creator_name}, description={self.description})>"

    def to_dict(self):
        return {
            'id': self.id,
            'creator_name': self.creator_name,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),  # Format datetime as ISO string
            'known_items': [item.to_dict() for item in self.known_items]  # Serialize known items if needed
        }

from .KnownItem import KnownItem

@event.listens_for(Knowledge, 'after_update')
def update_known_items(mapper, connection, target):
    known_items = KnownItem.query.filter_by(knowledgename=target.name).all()
    
    for item in known_items:
        item.knowledgename = target.name