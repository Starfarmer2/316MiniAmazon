from flask import Blueprint, render_template
from app.models.user import User

bp = Blueprint('user_routes', __name__)

@bp.route('/user/<int:user_id>/purchases')
def user_purchases(user_id):
    purchases = User.get_purchases(user_id)
    return render_template('user_purchases.html', purchases=purchases)
