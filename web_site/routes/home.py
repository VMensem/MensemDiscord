from flask import Blueprint, render_template

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    tools = [
        {"name": "Embed Builder", "status": "✅", "link": "/embeds"},
        {"name": "Ticket Builder", "status": "🚧 Скоро"},
        {"name": "Welcome Builder", "status": "🚧 Скоро"},
        {"name": "Banner Builder", "status": "🚧 Скоро"},
    ]
    return render_template('index.html', tools=tools)
