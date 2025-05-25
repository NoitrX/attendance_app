from .auth_routes import auth, init_auth
from .admin_routes import admin

def init_routes(app):
    init_auth(app)  
    app.register_blueprint(auth)
    app.register_blueprint(admin)

