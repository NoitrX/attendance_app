from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db


class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    schedule_title = db.Column(db.String(255), nullable=False)
    start_time = db.Column(db.String(50), nullable=False)  
    end_time = db.Column(db.String(50), nullable=False)  
    status = db.Column(db.String(50), nullable=False)
    timestamps = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Schedule {self.schedule_title}>'