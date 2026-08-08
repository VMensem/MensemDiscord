from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev_key')

    # Register Blueprints
    from .routes.home import home_bp
    from .routes.embeds import embeds_bp
    
    app.register_blueprint(home_bp)
    app.register_blueprint(embeds_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
