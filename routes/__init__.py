def init_routes(app):
    from .auth_routes import auth
    app.register_blueprint(auth)