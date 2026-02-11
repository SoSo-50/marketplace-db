from flask import Flask
from .extensions import db, jwt
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    from .routes.views import bp as views_bp
    from .routes.auth import bp as auth_bp
    from .routes.products import bp as products_bp
    from .routes.orders import bp as orders_bp
    from .routes.admin import bp as admin_bp

    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(products_bp, url_prefix='/api')
    app.register_blueprint(orders_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')

    return app