from models import db

class Biometric(db.Model):
    __tablename__ = 'biometrics'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    face_encoding = db.Column(db.LargeBinary, nullable=False)