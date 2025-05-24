import os

class Config:
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:@localhost/attendance_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'Uploads')
    CAPTURE_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'Captures')