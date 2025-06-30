from flask import Flask
from config import Config
from db import close_conn

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from auth.routes import bp as auth_bp
    from pedidos.routes import bp as pedidos_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pedidos_bp)

    app.teardown_appcontext(close_conn)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
