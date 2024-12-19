from app import db

class KnowledgeType(db.Model):
    __tablename__ = 'knowledgetypes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<KnowledgeType(name={self.name}, description={self.description})>"