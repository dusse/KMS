from app import db    
from .ProgressStatus import ProgressStatus
from .Biblio import Biblio
from .KnownItemVersion import KnownItemVersion
import os
from sqlalchemy import event
from flask import current_app

from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType

class KnownItem(db.Model):
    __tablename__ = 'knownitems'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    imgsrc = db.Column(db.String(100), nullable=True)
    content = db.Column(db.Text, nullable=True)

    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=True)

    knowledgename = db.Column(db.String(100), db.ForeignKey('knowledges.name', onupdate='CASCADE'), nullable=False)
    typename = db.Column(db.String(50), db.ForeignKey('knowledgetypes.name'), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    
    progress_status = db.Column(db.Enum(ProgressStatus), default=ProgressStatus.inprogress, nullable=False)

    order = db.Column(db.Integer, nullable=False, default=-1)

    knowledge = db.relationship('Knowledge', back_populates='known_items')
    file = db.relationship('File')

    bibliography_ids = db.Column(MutableList.as_mutable(PickleType), default=[])

    versions = db.relationship('KnownItemVersion', back_populates='known_item', cascade='all, delete-orphan')

    # Method to create a new version
    def create_new_version(self, modified_by, version_number=None):
        version = KnownItemVersion(
            known_item_id=self.id,
            version_number=version_number or (len(self.versions) + 1),
            name=self.name,
            description=self.description,
            content=self.content,
            modified_by=modified_by
        )
        db.session.add(version)
        db.session.commit()


    def __init__(self, *args, **kwargs):
        super(KnownItem, self).__init__(*args, **kwargs)
        if self.bibliography_ids is None:
            self.bibliography_ids = []

    def __repr__(self):
        return f"<KnownItem(name={self.name}, description={self.description})>"

    def add_bibliography(self, bibliography):
        if self.bibliography_ids is None:
            self.bibliography_ids = []
        if bibliography.id not in self.bibliography_ids:
            self.bibliography_ids.append(bibliography.id)

    def remove_bibliography(self, bibliography):
        """Remove a bibliography from the KnownItem by its ID."""
        if self.bibliography_ids and bibliography.id in self.bibliography_ids:
            self.bibliography_ids.remove(bibliography.id)

    def get_bibliographies(self):
        """Retrieve Biblio objects by their IDs."""
        if not self.bibliography_ids:
            return []

        return Biblio.query.filter(Biblio.id.in_(self.bibliography_ids)).all()


    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'imgsrc': self.imgsrc,
            'content': self.content,
            'file_id': self.file_id,
            'knowledgename': self.knowledgename,
            'typename': self.typename,
            'created_at': self.created_at.isoformat(),
            'progress_status': self.progress_status.name,
            'bibliographies': [b.to_dict() for b in self.get_bibliographies()]
        }



    @staticmethod
    def delete_file(filename):
        """Helper function to delete a file from the filesystem."""
        try:
            file_path = os.path.join(current_app.static_folder, 'uploads', filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            current_app.logger.error(f"Error deleting file {filename}: {e}")




@event.listens_for(KnownItem, 'before_delete')
def before_knowledge_delete(mapper, connection, target):
    """Delete the associated files when deleting the KnownItem."""
    if target.imgsrc:
        # Delete the image file if it exists
        target.delete_file(target.imgsrc)
    
    if target.file:
        # Delete the file if it exists
        target.delete_file(target.file.filename)

