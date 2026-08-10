from flask import Flask, send_from_directory, jsonify
import os

def create_app():
    app = Flask(__name__, static_folder='.')

    @app.route('/')
    def home():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/health')
    def health():
        return jsonify(status="ok"), 200

    return app
