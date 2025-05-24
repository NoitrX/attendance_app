from routes.auth_routes import auth, init_auth

def init_routes(app):
    init_auth(app)  
    app.register_blueprint(auth)