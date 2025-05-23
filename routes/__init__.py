from .auth_routes import auth
from .admin_routes import admin

def init_routes(app):
    app.register_blueprint(auth)
    app.register_blueprint(admin)
