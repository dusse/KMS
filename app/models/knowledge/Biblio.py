from app import db

class Biblio(db.Model):
    __tablename__ = 'bibliographies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=True)
    year = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    authors = db.Column(db.String(255), nullable=True)
    bibtex = db.Column(db.Text, nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=True)

    file = db.relationship('File', backref='bibliographies')


    def __repr__(self):
        return f"<Bibliography(title={self.title}, year={self.year})>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'year': self.year,
            'title': self.title,
            'authors': self.authors,
            'bibtex': self.bibtex,            
            'file_id': self.file_id
        }