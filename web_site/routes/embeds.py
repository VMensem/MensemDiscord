from flask import Blueprint, render_template

embeds_bp = Blueprint('embeds', __name__)

@embeds_bp.route('/embeds')
def embeds():
    return render_template('embeds.html')
