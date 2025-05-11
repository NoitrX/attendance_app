from models import db
import bcrypt

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    identifier = db.Column(db.String(50), unique=True, nullable=False)
    biometrics = db.relationship('Biometric', backref='user', lazy=True)
    attendances = db.relationship('Attendance', backref='user', lazy=True)