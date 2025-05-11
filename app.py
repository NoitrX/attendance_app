from flask import Flask
from config.config import Config
from models import db
from routes import init_routes
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)


    db.init_app(app)
    with app.app_context():
        db.create_all()


    init_routes(app)

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)