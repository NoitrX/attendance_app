from models import db
from datetime import datetime

class UserBiometric(db.Model):
    __tablename__ = 'user_biometrics'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    biometric = db.Column(db.Text, nullable=True)  
    image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user = db.relationship('User', backref='biometrics')

    def __repr__(self):
        return f'<UserBiometric {self.id} for User {self.user_id}>'