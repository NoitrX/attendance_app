from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User  
from .user_biometric import UserBiometric
from .schedule import Schedule
from .user_attendance import UserAttendance