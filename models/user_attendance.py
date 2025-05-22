from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db

class UserAttendance(db.Model):
    __tablename__ = 'user_attendances'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    attendance_time = db.Column(db.String(50), nullable=False)  
    status = db.Column(db.String(50), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)

    user = db.relationship('User', backref='attendances')
    schedule = db.relationship('Schedule', backref='attendances')

    def __repr__(self):
        return f'<UserAttendance {self.id} for User {self.user_id}>'