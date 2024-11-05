from flask import render_template, jsonify, redirect, url_for, flash, request, abort, current_app as app
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

from flask import Blueprint
bp = Blueprint('users', __name__)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_auth(form.email.data, form.password.data)
        if user is None:
            flash('Invalid email or password')
            return redirect(url_for('users.login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index.index')

        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/account')
@login_required
def account():
    recent_product_reviews = ProductReview.get_recent_by_user(current_user.userid)
    recent_seller_reviews = SellerReview.get_recent_by_user(current_user.userid)
    return render_template('account.html', 
                           user=current_user, 
                           recent_product_reviews=recent_product_reviews,
                           recent_seller_reviews=recent_seller_reviews)

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
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('users.login'))
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
    flash(f'Successfully deposited ${amount:.2f}')
    return redirect(url_for('users.account'))

@bp.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    amount = float(request.form['amount'])
    if amount <= current_user.balance:
        current_user.balance -= amount
        current_user.save()
        flash(f'Successfully withdrew ${amount:.2f}')
    else:
        flash('Insufficient funds')
    return redirect(url_for('users.account'))

@bp.route('/user/<int:user_id>/purchases')
@login_required
def user_purchases(user_id):
    if current_user.userid != user_id:
        flash('You can only view your own purchases.')
        return redirect(url_for('index.index'))

    # Using positional parameters (%s) instead of named parameters
    purchases = app.db.execute('''
        SELECT p.productid, p.prodname, pu.dtime, pu.quantity, pu.status, p.price
        FROM Purchases pu
        JOIN Products p ON pu.productid = p.productid
        WHERE pu.userid = :user_id
    ''', user_id=user_id,)  # Pass user_id as a tuple


    if not purchases:
        flash(f'No purchases found for your account.')
        return render_template('user_purchases.html', purchases=[])

    return render_template('user_purchases.html', purchases=purchases)



@bp.route('/user/<int:user_id>/profile')
@login_required
def user_profile(user_id):
    user = User.get(user_id)
    if user is None:
        abort(404)  # User not found
    
    # Get page number from request args, default to 1
    page = request.args.get('page', type=int, default=1)
    per_page = 20  # Number of items per page
    
    # Fetch seller's products if the user is a seller
    seller_products = Seller.get_seller_products(user_id)
    total = len(seller_products)
    
    # Calculate start and end indices for current page
    offset = (page - 1) * per_page
    end_idx = offset + per_page
    
    # Slice the products for current page
    products_for_page = seller_products[offset:end_idx] if seller_products else []

    # Create pagination object
    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=total,
        css_framework='bootstrap4',
        display_msg='Displaying <b>{start} - {end}</b> of <b>{total}</b> products'
    )

    # Rest of your existing code...
    ProductReviewInfo = namedtuple('ProductReviewInfo', [
        'productid', 'buyerid', 'dtime', 'review', 'rating', 
        'prodname', 'sellerid', 'seller_firstname', 'seller_lastname', 'product_url'
    ])
    product_reviews = app.db.execute('''
        SELECT pr.productid, pr.buyerid, pr.dtime, pr.review, pr.rating, 
               p.prodname, s.userid AS sellerid, s.firstname AS seller_firstname, s.lastname AS seller_lastname
        FROM ProductReviews pr
        JOIN Products p ON pr.productid = p.productid
        JOIN Sellers s ON p.sellerid = s.userid
        WHERE pr.buyerid = :user_id
        ORDER BY pr.dtime DESC
        LIMIT 5
    ''', user_id=user_id)
    recent_product_reviews = [
        ProductReviewInfo(*review, product_url=url_for('products.product_detail', product_id=review[0]))
        for review in product_reviews
    ]

    seller_reviews = SellerReview.get_recent_by_user(user_id)
    SellerReviewInfo = namedtuple('SellerReviewInfo', ['review', 'seller_firstname', 'seller_lastname'])
    recent_seller_reviews = []
    for review in seller_reviews:
        seller = User.get(review.sellerid)
        seller_firstname = seller.firstname if seller else "Unknown"
        seller_lastname = seller.lastname if seller else "Seller"
        review_info = SellerReviewInfo(review, seller_firstname, seller_lastname)
        recent_seller_reviews.append(review_info)

    return render_template('user_profile.html', 
                           profile_user=user,
                           recent_product_reviews=recent_product_reviews,
                           recent_seller_reviews=recent_seller_reviews,
                           seller_products=products_for_page,
                           pagination=pagination,
                           total=total,
                           per_page=per_page)  # Add this line


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
