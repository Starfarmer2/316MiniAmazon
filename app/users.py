from flask import render_template, send_file, jsonify, redirect, url_for, flash, request, abort, current_app as app
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from flask_paginate import Pagination, get_page_parameter
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from .models.user import User
from .models.product_review import ProductReview
from .models.sellerreview import SellerReview
from .models.product import Product
from .models.seller import Seller
from collections import namedtuple
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from flask import flash, redirect, url_for, request
import os
from flask import Blueprint
bp = Blueprint('users', __name__)
PRODUCTS_PER_PAGE = 20


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

@bp.route('/profile_image/<path:filename>')
def serve_profile_image(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return send_file(file_path)
    except FileNotFoundError:
        return redirect(url_for('static', filename='images/default-profile.png')), 303
    except Exception as e:
        app.logger.error(f"Error serving image {filename}: {str(e)}")
        return redirect(url_for('static', filename='images/default-profile.png')), 303


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_auth(form.email.data, form.password.data)
        if user is None:
            return """
                <style>
                    .toast {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background-color: white;
                        padding: 15px 25px;
                        border-radius: 5px;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        z-index: 1000;
                        animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                        border-left: 4px solid red;
                    }
                    @keyframes slideIn {
                        from {transform: translateX(100%);}
                        to {transform: translateX(0);}
                    }
                    @keyframes fadeOut {
                        from {opacity: 1;}
                        to {opacity: 0;}
                    }
                </style>
                <div class="toast">Invalid username or password. </div>
                <script>
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 1000);
                </script>
            """
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index.index')

        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')

    # Fetch the current password hash from the database
    password_row = app.db.execute("""
        SELECT password FROM Users
        WHERE userid = :userid
    """, userid=current_user.userid) 

    if not password_row:
        return """
            <style>
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: white;
                    padding: 15px 25px;
                    border-radius: 5px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    z-index: 1000;
                    animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                    border-left: 4px solid #f44336;
                }
                @keyframes slideIn {
                    from {transform: translateX(100%);}
                    to {transform: translateX(0);}
                }
                @keyframes fadeOut {
                    from {opacity: 1;}
                    to {opacity: 0;}
                }
            </style>
            <div class="toast">Error retrieving user password.</div>
            <script>
                setTimeout(() => {
                    window.location.href = '/account';
                }, 1000);
            </script>
        """


    stored_password_hash = password_row[0][0]

    if not check_password_hash(stored_password_hash, current_password):
        return """
            <style>
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: white;
                    padding: 15px 25px;
                    border-radius: 5px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    z-index: 1000;
                    animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                    border-left: 4px solid #f44336;
                }
                @keyframes slideIn {
                    from {transform: translateX(100%);}
                    to {transform: translateX(0);}
                }
                @keyframes fadeOut {
                    from {opacity: 1;}
                    to {opacity: 0;}
                }
            </style>
            <div class="toast">Current password in incorrect.</div>
            <script>
                setTimeout(() => {
                    window.location.href = '/account';
                }, 1000);
            </script>
        """

    if new_password != confirm_new_password:
        return """
            <style>
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: white;
                    padding: 15px 25px;
                    border-radius: 5px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    z-index: 1000;
                    animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                    border-left: 4px solid #f44336;
                }
                @keyframes slideIn {
                    from {transform: translateX(100%);}
                    to {transform: translateX(0);}
                }
                @keyframes fadeOut {
                    from {opacity: 1;}
                    to {opacity: 0;}
                }
            </style>
            <div class="toast">New passwords do not match. </div>
            <script>
                setTimeout(() => {
                    window.location.href = '/account';
                }, 1000);
            </script>
        """

    # Update the password in the database
    new_password_hash = generate_password_hash(new_password)
    app.db.execute("""
        UPDATE Users
        SET password = :password
        WHERE userid = :userid
    """, password=new_password_hash, userid=current_user.userid)

    return """
        <style>
            .toast {
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: white;
                padding: 15px 25px;
                border-radius: 5px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                z-index: 1000;
                animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                border-left: 4px solid #f44336;
            }
            @keyframes slideIn {
                from {transform: translateX(100%);}
                to {transform: translateX(0);}
            }
            @keyframes fadeOut {
                from {opacity: 1;}
                to {opacity: 0;}
            }
        </style>
        <div class="toast">Password updated successfully.</div>
        <script>
            setTimeout(() => {
                window.location.href = '/account';
            }, 1000);
        </script>
    """


@bp.route('/register_seller', methods=['POST'])
@login_required
def register_seller():
    # Check if the user is already a seller
    rows = app.db.execute("""
        SELECT UserID FROM Sellers
        WHERE UserID = :userid
    """, userid=current_user.userid)

    if len(rows) > 0:
        return """
            <style>
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: white;
                    padding: 15px 25px;
                    border-radius: 5px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    z-index: 1000;
                    animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                    border-left: 4px solid #f44336;
                }
                @keyframes slideIn {
                    from {transform: translateX(100%);}
                    to {transform: translateX(0);}
                }
                @keyframes fadeOut {
                    from {opacity: 1;}
                    to {opacity: 0;}
                }
            </style>
            <div class="toast">You are already registered as a seller. </div>
            <script>
                setTimeout(() => {
                    window.location.href = '/account';
                }, 1000);
            </script>
        """

    # Retrieve the password hash directly from the Users table
    password_row = app.db.execute("""
        SELECT password FROM Users
        WHERE userid = :userid
    """, userid=current_user.userid)

    if not password_row:
        return """
            <style>
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: white;
                    padding: 15px 25px;
                    border-radius: 5px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    z-index: 1000;
                    animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                    border-left: 4px solid #f44336;
                }
                @keyframes slideIn {
                    from {transform: translateX(100%);}
                    to {transform: translateX(0);}
                }
                @keyframes fadeOut {
                    from {opacity: 1;}
                    to {opacity: 0;}
                }
            </style>
            <div class="toast">Error retrieving user password. </div>
            <script>
                setTimeout(() => {
                    window.location.href = '/account';
                }, 1000);
            </script>
        """

    password_hash = password_row[0][0]  # Get the hashed password from the result

    # Insert the user into the Sellers table
    app.db.execute("""
        INSERT INTO Sellers(userid, email, firstname, lastname, address, password, balance)
        VALUES(:userid, :email, :firstname, :lastname, :address, :password, :balance)
    """, userid=current_user.userid,
       email=current_user.email,
       firstname=current_user.firstname,
       lastname=current_user.lastname,
       address=current_user.address,
       password=password_hash,  # assuming password is already hashed
       balance=current_user.balance)

    return """
        <style>
            .toast {
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: white;
                padding: 15px 25px;
                border-radius: 5px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                z-index: 1000;
                animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                border-left: 4px solid #f44336;
            }
            @keyframes slideIn {
                from {transform: translateX(100%);}
                to {transform: translateX(0);}
            }
            @keyframes fadeOut {
                from {opacity: 1;}
                to {opacity: 0;}
            }
        </style>
        <div class="toast">Successfully registered as a seller! </div>
        <script>
            setTimeout(() => {
                window.location.href = '/account';
            }, 1000);
        </script>
    """


@bp.route('/account')
@login_required
def account():
    recent_product_reviews = ProductReview.get_recent_by_user(current_user.userid)
    recent_seller_reviews = SellerReview.get_recent_by_user(current_user.userid)
    rows = app.db.execute("""
        SELECT UserID FROM Sellers
        WHERE UserID = :userid
    """, userid=current_user.userid)

    # If rows are returned, the user is a seller
    is_seller = len(rows) > 0
    return render_template('account.html', 
                       user=current_user, 
                       recent_product_reviews=recent_product_reviews,
                       recent_seller_reviews=recent_seller_reviews,
                       is_seller=is_seller)


class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(),
                                       EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        if User.email_exists(email.data):
            raise ValidationError('Already a user with this email.')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.register(form.email.data,
                         form.password.data,
                         form.firstname.data,
                         form.lastname.data):
            return """
                <style>
                    .toast {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background-color: white;
                        padding: 15px 25px;
                        border-radius: 5px;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        z-index: 1000;
                        animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                        border-left: 4px solid red;
                    }
                    @keyframes slideIn {
                        from {transform: translateX(100%);}
                        to {transform: translateX(0);}
                    }
                    @keyframes fadeOut {
                        from {opacity: 1;}
                        to {opacity: 0;}
                    }
                </style>
                <div class="toast">Congratulations, you are now a registered user! </div>
                <script>
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 1000);
                </script>
            """

    return render_template('register.html', title='Register', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index.index'))

@bp.route('/deposit', methods=['POST'])
@login_required
def deposit():
    amount = float(request.form['amount'])
    current_user.balance += amount
    current_user.save()
    return f"""
        <style>
            .toast {{
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: white;
                padding: 15px 25px;
                border-radius: 5px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                z-index: 1000;
                animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                border-left: 4px solid green;
            }}
            @keyframes slideIn {{
                from {{transform: translateX(100%);}}
                to {{transform: translateX(0);}}
            }}
            @keyframes fadeOut {{
                from {{opacity: 1;}}
                to {{opacity: 0;}}
            }}
        </style>
        <div class="toast">Successfully deposited ${amount:.2f} </div>
        <script>
            setTimeout(() => {{
                window.location.href = '/account';
            }}, 1000);
        </script>
    """

@bp.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    amount = float(request.form['amount'])
    if amount <= current_user.balance:
        current_user.balance -= amount
        current_user.save()
        return f"""
            <style>
                .toast {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: white;
                    padding: 15px 25px;
                    border-radius: 5px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    z-index: 1000;
                    animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                    border-left: 4px solid green;
                }}
                @keyframes slideIn {{
                    from {{transform: translateX(100%);}}
                    to {{transform: translateX(0);}}
                }}
                @keyframes fadeOut {{
                    from {{opacity: 1;}}
                    to {{opacity: 0;}}
                }}
            </style>
            <div class="toast">Successfully withdrew ${amount:.2f} </div>
            <script>
                setTimeout(() => {{
                    window.location.href = '/account';
                }}, 1000);
            </script>
        """
    else:
        return f"""
            <style>
                .toast {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: white;
                    padding: 15px 25px;
                    border-radius: 5px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    z-index: 1000;
                    animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                    border-left: 4px solid green;
                }}
                @keyframes slideIn {{
                    from {{transform: translateX(100%);}}
                    to {{transform: translateX(0);}}
                }}
                @keyframes fadeOut {{
                    from {{opacity: 1;}}
                    to {{opacity: 0;}}
                }}
            </style>
            <div class="toast">Insufficient funds.</div>
            <script>
                setTimeout(() => {{
                    window.location.href = '/account';
                }}, 1000);
            </script>
        """
    return redirect(url_for('users.account'))

@bp.route('/user/<int:user_id>/purchases')
@login_required
def user_purchases(user_id):
    if current_user.userid != user_id:
        # flash('You can only view your own purchases.')
        return redirect(url_for('index.index'))

    # Retrieve optional filter parameters from query string
    product_name = request.args.get('product_name')
    seller_name = request.args.get('seller_name')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')

    # Build query dynamically based on filters provided
    query = '''
        SELECT DISTINCT p.productid, p.prodname, pu.dtime, pu.quantity, pu.status, p.price, s.firstname AS seller_firstname, s.lastname AS seller_lastname
        FROM Purchases pu
        JOIN Products p ON pu.productid = p.productid
        JOIN Sellers s ON p.sellerid = s.userid
        WHERE pu.userid = :user_id
    '''
    params = {'user_id': user_id}

    # Add filter conditions based on provided parameters
    if product_name:
        query += ' AND p.prodname ILIKE :product_name'
        params['product_name'] = f'%{product_name}%'
    if seller_name:
        query += ' AND (s.firstname || \' \' || s.lastname) ILIKE :seller_name'
        params['seller_name'] = f'%{seller_name}%'
    if start_date:
        query += ' AND pu.dtime >= :start_date'
        params['start_date'] = start_date
    if end_date:
        query += ' AND pu.dtime <= :end_date'
        params['end_date'] = end_date
    if status is not None and status != '':
        params['status'] = bool(int(status))  # Convert to boolean if status is passed as '0' or '1'
        query += ' AND pu.status = :status'

    # Execute the query with the dynamically built parameters
    purchases = app.db.execute(query, **params)

    if not purchases:
        # flash('No purchases found for your filters.')
        return render_template('user_purchases.html', purchases=[])

    return render_template('user_purchases.html', purchases=purchases)

@bp.route('/user/<int:user_id>/purchase_summary')
@login_required
def purchase_summary(user_id):
    if current_user.userid != user_id:
        # flash('You can only view your own purchases.')
        return redirect(url_for('index.index'))

    # Retrieve filter parameters from query string (passed from user_purchases or directly by the user)
    product_name = request.args.get('product_name')
    seller_name = request.args.get('seller_name')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')

    # Base query to get the total quantity of purchases by category with filters
    query = '''
        SELECT p.category, SUM(pu.quantity) AS total_quantity
        FROM Purchases pu
        JOIN Products p ON pu.productid = p.productid
        JOIN Sellers s ON p.sellerid = s.userid
        WHERE pu.userid = :user_id
    '''
    params = {'user_id': user_id}

    # Apply filters based on query parameters
    if product_name:
        query += ' AND p.prodname ILIKE :product_name'
        params['product_name'] = f'%{product_name}%'
    if seller_name:
        query += ' AND (s.firstname || \' \' || s.lastname) ILIKE :seller_name'
        params['seller_name'] = f'%{seller_name}%'
    if start_date:
        query += ' AND pu.dtime >= :start_date'
        params['start_date'] = start_date
    if end_date:
        query += ' AND pu.dtime <= :end_date'
        params['end_date'] = end_date
    if status is not None and status != '':
        params['status'] = bool(int(status))  # Convert to boolean if status is passed as '0' or '1'
        query += ' AND pu.status = :status'

    # Group by category and sort by total quantity
    query += ' GROUP BY p.category ORDER BY total_quantity DESC'

    # Execute the query with the dynamically built parameters
    summary_data = app.db.execute(query, **params)

    # Query to get detailed purchase information with the same filters
    detailed_query = '''
        SELECT p.productid, p.prodname, pu.dtime, pu.quantity, pu.status, p.price,
               p.category, s.firstname AS seller_firstname, s.lastname AS seller_lastname, p.imagepath
        FROM Purchases pu
        JOIN Products p ON pu.productid = p.productid
        JOIN Sellers s ON p.sellerid = s.userid
        WHERE pu.userid = :user_id
    '''
    
    # Apply the same filters to the detailed query
    detailed_query += query[query.index('AND'):query.index('GROUP BY')] if 'AND' in query else ''
    detailed_query += ' ORDER BY pu.dtime DESC'

    # Execute the detailed query
    detailed_purchases = app.db.execute(detailed_query, **params)

    # Convert data into JSON format
    categories = [row[0] for row in summary_data]
    purchase_counts = [row[1] for row in summary_data]

    purchases = [
        {
            "product_id": row[0],
            "product_name": row[1],
            "purchase_time": row[2],
            "quantity": row[3],
            "status": row[4],
            "price": row[5],
            "category": row[6],
            "seller_name": f"{row[7]} {row[8]}",
            "imagepath": row[9]
        }
        for row in detailed_purchases
    ]

    return jsonify({"categories": categories, "purchase_counts": purchase_counts, "purchases": purchases})

@bp.route('/user/<int:user_id>/profile')
@login_required
def user_profile(user_id):
    user = User.get(user_id)
    if user is None:
        abort(404)
    
    # Fetch seller's products with pagination
    page = request.args.get('page', type=int, default=1)
    per_page = 20

    # Get total count of seller's products
    total_count = app.db.execute('''
        SELECT COUNT(*) 
        FROM Products 
        WHERE sellerid = :sellerid
    ''', sellerid=user_id)
    total = total_count[0][0] if total_count else 0

    # Get paginated products
    seller_products = app.db.execute('''
        SELECT productid, sellerid, prodname, description, 
               imagepath, price, quantity, category
        FROM Products
        WHERE sellerid = :sellerid
        ORDER BY productid
        LIMIT :limit OFFSET :offset
    ''', 
        sellerid=user_id,
        limit=per_page,
        offset=(page - 1) * per_page
    )

    # Create pagination object
    from flask_paginate import Pagination
    pagination = Pagination(
        page=page,
        total=total,
        per_page=per_page,
        css_framework='bootstrap4'
    )

    # Get seller reviews with full user information
    seller_reviews = app.db.execute('''
        SELECT 
            sr.buyerid,
            sr.sellerid,
            sr.dtime,
            sr.rating,
            sr.review,
            buyer.firstname AS buyer_firstname,
            buyer.lastname AS buyer_lastname,
            seller.firstname AS seller_firstname,
            seller.lastname AS seller_lastname
        FROM SellerReviews sr
        JOIN Users buyer ON sr.buyerid = buyer.userid
        JOIN Users seller ON sr.sellerid = seller.userid
        WHERE sr.sellerid = :sellerid
        ORDER BY sr.dtime DESC
        LIMIT 5
    ''', sellerid=user_id)

    Review = namedtuple('Review', ['review', 'sellerid', 'dtime', 'rating'])
    SellerReviewInfo = namedtuple('SellerReviewInfo', [
        'review', 'seller_firstname', 'seller_lastname',
        'buyer_firstname', 'buyer_lastname'
    ])
    
    
    recent_seller_reviews = []
    for review in seller_reviews:
        review_obj = Review(
            review=review.review,
            sellerid=review.sellerid,
            dtime=review.dtime,
            rating=review.rating
        )
        review_info = SellerReviewInfo(
            review=review_obj,
            seller_firstname=review.seller_firstname,
            seller_lastname=review.seller_lastname,
            buyer_firstname=review.buyer_firstname,
            buyer_lastname=review.buyer_lastname
        )
        recent_seller_reviews.append(review_info)

    # Get product reviews
    product_reviews = app.db.execute('''
        SELECT 
            pr.productid,
            pr.buyerid,
            pr.dtime,
            pr.review,
            pr.rating,
            p.prodname,
            s.userid AS sellerid,
            s.firstname AS seller_firstname,
            s.lastname AS seller_lastname
        FROM ProductReviews pr
        JOIN Products p ON pr.productid = p.productid
        JOIN Sellers s ON p.sellerid = s.userid
        WHERE pr.buyerid = :user_id
        ORDER BY pr.dtime DESC
        LIMIT 5
    ''', user_id=user_id)

    ProductReviewInfo = namedtuple('ProductReviewInfo', [
        'productid', 'buyerid', 'dtime', 'review', 'rating', 
        'prodname', 'sellerid', 'seller_firstname', 'seller_lastname', 'product_url'
    ])

    recent_product_reviews = [
        ProductReviewInfo(
            *review,
            product_url=url_for('products.product_detail', product_id=review.productid)
        )
        for review in product_reviews
    ]

    # Check if current user has purchased from this seller
    has_purchased_from_seller = False
    if current_user.is_authenticated and current_user.userid != user_id:
        purchase_check = app.db.execute('''
            SELECT COUNT(*) 
            FROM Purchases p
            JOIN Products prod ON p.productid = prod.productid
            WHERE p.userid = :userid AND prod.sellerid = :sellerid
        ''', userid=current_user.userid, sellerid=user_id)
        has_purchased_from_seller = purchase_check[0][0] > 0 if purchase_check else False

    existing_review = None
    if current_user.is_authenticated:
        review_check = app.db.execute('''
            SELECT rating, review 
            FROM SellerReviews 
            WHERE buyerid = :buyerid AND sellerid = :sellerid
        ''', buyerid=current_user.userid, sellerid=user_id)
        if review_check:
            existing_review = {
                'rating': review_check[0][0],
                'review': review_check[0][1]
            }

    # Get seller review stats
    seller_stats = app.db.execute('''
        SELECT AVG(rating) as avg_rating, COUNT(*) as review_count
        FROM SellerReviews
        WHERE sellerid = :sellerid
    ''', sellerid=user_id)
    
    seller_rating = round(seller_stats[0][0], 1) if seller_stats[0][0] else None
    seller_review_count = seller_stats[0][1]
    
    return render_template('user_profile.html',
                         profile_user=user,
                         recent_product_reviews=recent_product_reviews,
                         recent_seller_reviews=recent_seller_reviews,
                         has_purchased_from_seller=has_purchased_from_seller,
                         seller_products=seller_products,
                         pagination=pagination,
                         total=total,
                         existing_review=existing_review,
                         seller_rating=seller_rating,
                         seller_review_count=seller_review_count,
                         per_page=per_page)

@bp.route('/api/seller/<int:sellerid>/products', methods=['GET'])
@login_required
def get_seller_products_api(sellerid):
    try:
        # Call the function to get the seller's products
        products = Seller.get_seller_products(sellerid)

        # Return the products in JSON format
        return jsonify(products), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/delete_product_review/<int:product_id>', methods=['POST'])
@login_required
def delete_product_review(product_id):
    print(f"Delete product review route accessed for product_id: {product_id}")  # Debug print
    try:
        result = app.db.execute('''
            DELETE FROM ProductReviews 
            WHERE productid = :productid 
            AND buyerid = :buyerid
        ''', 
        productid=product_id,
        buyerid=current_user.userid)
        
        print(f"Delete result: {result}")  # Debug print
        return f"""
            <style>
                .toast {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: white;
                    padding: 15px 25px;
                    border-radius: 5px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    z-index: 1000;
                    animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                    border-left: 4px solid #f44336;
                }}
                @keyframes slideIn {{
                    from {{transform: translateX(100%);}}
                    to {{transform: translateX(0);}}
                }}
                @keyframes fadeOut {{
                    from {{opacity: 1;}}
                    to {{opacity: 0;}}
                }}
            </style>
            <div class="toast">Review deleted successfully.</div>
            <script>
                setTimeout(() => {{
                    window.location.href = '/product/${product_id}';
                }}, 1000);
            </script>
        """

    except Exception as e:
        print(f"Error in delete_product_review: {str(e)}")  
        return f"""
            <style>
                .toast {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: white;
                    padding: 15px 25px;
                    border-radius: 5px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    z-index: 1000;
                    animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                    border-left: 4px solid #f44336;
                }}
                @keyframes slideIn {{
                    from {{transform: translateX(100%);}}
                    to {{transform: translateX(0);}}
                }}
                @keyframes fadeOut {{
                    from {{opacity: 1;}}
                    to {{opacity: 0;}}
                }}
            </style>
            <div class="toast">Error in deleting review.</div>
            <script>
                setTimeout(() => {{
                    window.location.href = '/product/${product_id}';
                }}, 1000);
            </script>
        """
    
@bp.route('/seller/<int:seller_id>/review', methods=['POST'])
@login_required
def add_seller_review(seller_id):
    print(f"Received review submission for seller {seller_id}")
    print(f"Form data: {request.form}")
    
    # Get the return_to parameter and product_id if they exist
    return_to = request.args.get('return_to')
    product_id = request.args.get('product_id')
    
    if not request.form.get('rating') or not request.form.get('review'):
        # flash('Both rating and review are required.')
        if return_to == 'product':
            return redirect(url_for('products.product_detail', product_id=product_id))
        return redirect(url_for('users.user_profile', user_id=seller_id))
    
    # Check if user has purchased from this seller
    purchase_check = app.db.execute('''
        SELECT COUNT(*) 
        FROM Purchases p
        JOIN Products prod ON p.productid = prod.productid
        WHERE p.userid = :userid AND prod.sellerid = :sellerid
    ''', userid=current_user.userid, sellerid=seller_id)
    
    print(f"Purchase check result: {purchase_check}")
    
    if not purchase_check or purchase_check[0][0] == 0:
        # flash('You can only review sellers you have purchased from.')
        if return_to == 'product':
            return redirect(url_for('products.product_detail', product_id=product_id))
        return redirect(url_for('users.user_profile', user_id=seller_id))
    
    try:
        # Check for existing review
        existing_review = app.db.execute('''
            SELECT COUNT(*) 
            FROM SellerReviews 
            WHERE buyerid = :userid AND sellerid = :sellerid
        ''', userid=current_user.userid, sellerid=seller_id)
        
        current_time = datetime.now()
        
        if existing_review and existing_review[0][0] > 0:
            # Update existing review
            app.db.execute('''
                UPDATE SellerReviews 
                SET rating = :rating, review = :review, dtime = :dtime
                WHERE buyerid = :userid AND sellerid = :sellerid
            ''', 
                rating=int(request.form['rating']),
                review=request.form['review'],
                dtime=current_time,
                userid=current_user.userid,
                sellerid=seller_id)
            # flash('Your seller review has been updated.')
        else:
            # Create new review
            print("Creating new review")
            app.db.execute('''
                INSERT INTO SellerReviews(buyerid, sellerid, dtime, rating, review)
                VALUES(:buyerid, :sellerid, :dtime, :rating, :review)
            ''',
                buyerid=current_user.userid,
                sellerid=seller_id,
                dtime=current_time,
                rating=int(request.form['rating']),
                review=request.form['review'])
            # flash('Your seller review has been added successfully.')
            
    except Exception as e:
        print(f"Error saving seller review: {str(e)}")
        # flash(f'Error saving seller review: {str(e)}')
    
    if return_to == 'product':
        return redirect(url_for('products.product_detail', product_id=product_id))
    return redirect(url_for('users.user_profile', user_id=seller_id))

@bp.route('/delete_seller_review/<int:seller_id>', methods=['POST'])
@login_required
def delete_seller_review(seller_id):
    print(f"Delete seller review route accessed for seller_id: {seller_id}")
    
    # Get the return_to parameter and product_id if they exist
    return_to = request.args.get('return_to')
    product_id = request.args.get('product_id')
    
    try:
        result = app.db.execute('''
            DELETE FROM SellerReviews 
            WHERE sellerid = :sellerid 
            AND buyerid = :buyerid
        ''', 
        sellerid=seller_id,
        buyerid=current_user.userid)
        
        print(f"Delete result: {result}")
        # flash('Review deleted successfully')


        
    except Exception as e:
        print(f"Error in delete_seller_review: {str(e)}")
        # flash('Error deleting review')
    
    if return_to == 'product':
        return redirect(url_for('products.product_detail', product_id=product_id))
    return redirect(url_for('users.user_profile', user_id=seller_id))

@bp.route('/toggle-seller-helpful', methods=['POST'])
@login_required
def toggle_seller_helpful():
    try:
        reviewid = request.form.get('reviewid')
        seller_id = request.form.get('seller_id')
        return_to = request.form.get('return_to')
        product_id = request.form.get('product_id')
        
        # Check if already marked
        marked = app.db.execute('''
            SELECT 1 FROM MarkedSellerReviewHelpful 
            WHERE reviewid = :reviewid AND user_id = :user_id
        ''', reviewid=reviewid, user_id=current_user.userid)
        
        if marked:
            app.db.execute('''
                DELETE FROM MarkedSellerReviewHelpful
                WHERE reviewid = :reviewid AND user_id = :user_id
            ''', reviewid=reviewid, user_id=current_user.userid)
            # flash('Removed helpful mark')
        else:
            app.db.execute('''
                INSERT INTO MarkedSellerReviewHelpful(reviewid, user_id)
                VALUES(:reviewid, :user_id)
            ''', reviewid=reviewid, user_id=current_user.userid)
            # flash('Marked as helpful')
        
        # Redirect based on where the request came from
        if return_to == 'product':
            return redirect(url_for('products.product_detail', product_id=product_id))
        else:
            return redirect(url_for('users.user_profile', user_id=seller_id))
        
    except Exception as e:
        print(f"Error in toggle_seller_helpful: {str(e)}")
        # flash('Error updating helpful status')
        return redirect(url_for('index.index'))


@bp.route('/update_account', methods=['POST'])
@login_required
def update_account():
    email = request.form.get('email')
    address = request.form.get('address')

    existing_email = app.db.execute("""
        SELECT userid FROM Users 
        WHERE email = :email AND userid != :userid
    """, email=email, userid=current_user.userid)

    if existing_email:
        return """
            <style>
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: white;
                    padding: 15px 25px;
                    border-radius: 5px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    z-index: 1000;
                    animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                    border-left: 4px solid #f44336;
                }
                @keyframes slideIn {
                    from {transform: translateX(100%);}
                    to {transform: translateX(0);}
                }
                @keyframes fadeOut {
                    from {opacity: 1;}
                    to {opacity: 0;}
                }
            </style>
            <div class="toast">Email address is already registered</div>
            <script>
                setTimeout(() => {
                    window.location.href = '/account';
                }, 1000);
            </script>
        """

    current_user.email = email
    current_user.address = address
    current_user.save()

    if current_user.is_seller():
        app.db.execute("""
            UPDATE Sellers
            SET email = :email,
                address = :address
            WHERE userid = :userid
        """, userid=current_user.userid, email=email, address=address)

    return """
        <style>
            .toast {
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: white;
                padding: 15px 25px;
                border-radius: 5px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                z-index: 1000;
                animation: slideIn 0.5s, fadeOut 0.5s 2.5s forwards;
                border-left: 4px solid #4CAF50;
            }
            @keyframes slideIn {
                from {transform: translateX(100%);}
                to {transform: translateX(0);}
            }
            @keyframes fadeOut {
                from {opacity: 1;}
                to {opacity: 0;}
            }
        </style>
        <div class="toast">Account updated successfully!</div>
        <script>
            setTimeout(() => {
                window.location.href = '/account';
            }, 1000);
        </script>
    """
