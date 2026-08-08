from flask import Blueprint, render_template


home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def index():
    tools = [
        {'name': 'Embed Builder', 'status': 'ready', 'link': '/embeds'},
        {'name': 'Ticket Builder', 'status': 'soon'},
        {'name': 'Banner Builder', 'status': 'soon'},
    ]
    return render_template('index.html', tools=tools)
