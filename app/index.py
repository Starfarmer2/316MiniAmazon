from flask import render_template
from flask_login import current_user
import datetime

from .models.product import Product
from .models.purchase import Purchase
from .models.user import User 

from flask import Blueprint
bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    # get all available products for sale:
    products = Product.get_all()
    # find the products current user has bought:
    if current_user.is_authenticated:
        # get purchase history
        purchases = Purchase.get_all_by_uid_since(
            current_user.userid, datetime.datetime(1980, 9, 14, 0, 0, 0))
        # get current balance 
        balance = User.get_balance(current_user.userid)[0][0]
        print(balance)

    else:
        purchases = None
        balance = 0
    # render the page by adding information to the index.html file
    return render_template('index.html',
                           avail_products=products,
                           purchase_history=purchases, 
                           balance=balance)