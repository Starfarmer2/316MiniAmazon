from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request, abort, current_app as app
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from .models.product import Product
from .models.product_review import ProductReview
from .models.user import User

bp = Blueprint('products', __name__)

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Add Product')

@bp.route('/products')
def all_products():
    products = Product.get_all()
    return render_template('products.html', products=products)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.get(product_id)
    if product is None:
        abort(404)
    
    seller = User.get(product.sellerid) if product is not None else abort(404)

    # Fetch reviews with reviewer names
    reviews = app.db.execute('''
        SELECT pr.productid, pr.buyerid, pr.dtime, pr.review, pr.rating,
               u.firstname, u.lastname
        FROM ProductReviews pr
        JOIN Users u ON pr.buyerid = u.userid
        WHERE pr.productid = :productid
        ORDER BY pr.dtime DESC
    ''', productid=product_id)

    return render_template('product_detail.html', 
                           product=product, 
                           seller=seller,
                           reviews=reviews)

@bp.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_seller:
        flash('You do not have permission to add products.')
        return redirect(url_for('products.all_products'))
    
    form = ProductForm()
    if form.validate_on_submit():
        if Product.add_product(form.name.data, form.price.data, form.quantity.data, form.description.data, current_user.id):
            flash('Product added successfully!')
            return redirect(url_for('products.all_products'))
    return render_template('add_product.html', form=form)

@bp.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.get(product_id)
    if product is None:
        flash('Product not found.')
        return redirect(url_for('products.all_products'))
    
    if product.sellerid != current_user.id:
        flash('You do not have permission to edit this product.')
        return redirect(url_for('products.product_detail', product_id=product_id))
    
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        if Product.update_product(product_id, form.name.data, form.price.data, form.quantity.data, form.description.data):
            flash('Product updated successfully!')
            return redirect(url_for('products.product_detail', product_id=product_id))
    return render_template('edit_product.html', form=form, product=product)

@bp.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.get(product_id)
    if product is None:
        flash('Product not found.')
        return redirect(url_for('products.all_products'))
    
    if product.seller_id != current_user.id:
        flash('You do not have permission to delete this product.')
        return redirect(url_for('products.product_detail', product_id=product_id))
    
    if Product.delete_product(product_id):
        flash('Product deleted successfully!')
    else:
        flash('Failed to delete product.')
    return redirect(url_for('products.all_products'))

@bp.route('/search')
def search_products():
    query = request.args.get('query', '')
    products = Product.search(query)
    return render_template('search_results.html', products=products, query=query)

# API end point for filtering products based on name and seller, not a real url link
@bp.route('/filter-products', methods=['POST'])
def filter_products():
    # Get JSON data from the request
    data = request.json
    seller_search_term = data.get('sellerSearchTerm', '').lower()
    product_search_term = data.get('productSearchTerm', '').lower()


    # Initialize a base query for products
    products = Product.get_all()  # Get all products

    # Filter by seller name if the term is provided
    if seller_search_term:
        products = Product.filter_by_seller(seller_search_term)

    #Now filter that on product search term if provided through list comprehension
    if product_search_term:
        products = [product for product in products if product_search_term in product.prodname.lower()]


    # Convert the query results into a list of dictionaries, only need to provide id. Includes the other two for debugging
    product_list = [
        {
            "id": product.productid,
            "name": product.prodname,
            "sellerid": product.sellerid,
        }
        for product in products
    ]

    # Return the list as a JSON response
    return jsonify(product_list)
