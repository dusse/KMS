from app import db
from datetime import datetime


class Theme(db.Model):
    __tablename__ = 'themes'
        
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    background_image = db.Column(db.String(255), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=False)
  
    def __repr__(self):
        return f"<Paper(id={self.id}, name='{self.name}')>"