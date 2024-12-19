from app import db
from datetime import datetime

class Log(db.Model):
    __tablename__ = 'logs'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    message = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Log(id={self.id}, message={self.message}, date={self.date})>"
