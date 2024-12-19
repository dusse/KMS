from app import db
from .Biblio import Biblio

class KnownItemVersion(db.Model):
    __tablename__ = 'knownitem_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    known_item_id = db.Column(db.Integer, db.ForeignKey('knownitems.id', ondelete='CASCADE'), nullable=False)
    
    # Version details
    version_number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)

    modified_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    modified_by = db.Column(db.String(100), nullable=True)
    
    known_item = db.relationship('KnownItem', back_populates='versions')


    def __repr__(self):
        return f"<KnownItemVersion(name={self.name}, description={self.description})>"


    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'content': self.content
        }



