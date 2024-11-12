from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request, abort, current_app as app
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from .models.product import Product
from .models.product_review import ProductReview
from .models.user import User
from math import ceil

bp = Blueprint('products', __name__)
PRODUCTS_PER_PAGE = 20

class ProductForm(FlaskForm):
    prodname = StringField('Product Name', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description', validators=[DataRequired()])
    image_path = StringField('Image Path') 
    category = StringField('Category') 
    submit = SubmitField('Add Product')

@bp.route('/products')
def all_products():
    # Get page number from query parameters, default to 1
    page = request.args.get('page', 1, type=int)
    
    # Get total number of products for pagination
    total_products = app.db.execute(
        'SELECT COUNT(*) FROM Products'
    )[0][0]
    
    # Calculate total pages
    total_pages = ceil(total_products / PRODUCTS_PER_PAGE)
    
    # Get paginated products
    products = app.db.execute('''
        SELECT *
        FROM Products
        ORDER BY productid
        LIMIT :limit OFFSET :offset
    ''', 
        limit=PRODUCTS_PER_PAGE,
        offset=(page - 1) * PRODUCTS_PER_PAGE
    )
    
    return render_template('products.html',
                         products=products,
                         current_page=page,
                         total_pages=total_pages)

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
    if not current_user.is_seller():
        flash('You do not have permission to add products.')
        return redirect(url_for('products.all_products'))
    
    form = ProductForm()
    if form.validate_on_submit():
        if Product.add_product(form.prodname.data, form.price.data, form.quantity.data, form.description.data, current_user.id, form.image_path.data, form.category.data):
            flash('Product added successfully!')
            return redirect(url_for('products.manage_inventory'))
    else:
        print("DID NOT ADD PRODUCT!(Failed form validate_on_submit)")
        print(form.errors)
    return render_template('manage_inventory.html', form=form)

@bp.route('/product/<int:product_id>/edit', methods=['POST'])
@login_required
def edit_product(product_id):
    product = Product.get(product_id)
    if product is None:
        flash('Product not found.')
        return redirect(url_for('products.all_products'))
    
    if product.sellerid != current_user.id:
        flash('You do not have permission to edit this product.')
        return redirect(url_for('products.product_detail', product_id=product_id))
    
    form = ProductForm()  # Using the same form for edit
    if form.validate_on_submit():
        # Update product in the database with the new form data
        if Product.update_product(
            product_id, 
            form.prodname.data, 
            form.price.data, 
            form.quantity.data, 
            form.description.data, 
            form.image_path.data,
            form.category.data
        ):
            flash('Product updated successfully!')
            return redirect(url_for('products.manage_inventory'))
    else:
        print("DID NOT EDIT PRODUCT!(Failed form validate_on_submit)")
        print(form.errors)
    # If form submission is invalid, re-render the form with errors
    return render_template('manage_inventory.html', form=form)



@bp.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.get(product_id)
    if product is None:
        flash('Product not found.')
        return redirect(url_for('products.all_products'))
    
    if product.sellerid != current_user.userid:
        flash('You do not have permission to delete this product.')
        return redirect(url_for('products.product_detail', product_id=product_id))
    
    if Product.delete_product(product_id):
        flash('Product deleted successfully!')
    else:
        flash('Failed to delete product.')
    return redirect(url_for('products.manage_inventory'))

@bp.route('/search')
def search_products():
    query = request.args.get('query', '')
    products = Product.search(query)
    return render_template('search_results.html', products=products, query=query)

@bp.route('/filter-products', methods=['POST'])
def filter_products():
    data = request.json
    seller_search_term = data.get('sellerSearchTerm', '').lower()
    product_search_term = data.get('productSearchTerm', '').lower()
    order_by = data.get('orderBy').lower()
    top_k = data.get('topK')

    print('orderBy:', order_by)
    
    # Build the base query
    query = '''
        SELECT p.*, u.firstname, u.lastname
        FROM Products p
        JOIN Users u ON p.sellerid = u.userid
        WHERE 1=1
    '''
    params = {}

    # Filtering/sorting a list of products: 
    # e.g., sorting by average review rating 
    # or total sales, filtering by rating, price, 
    # and/or availability of highly rated sellers,
    #  etc.
    
    # Add search conditions
    if product_search_term:
        query += ' AND LOWER(p.prodname) LIKE :product_term'
        params['product_term'] = f'%{product_search_term}%'
    
    if seller_search_term:
        query += ''' AND (LOWER(u.firstname) LIKE :seller_term 
                     OR LOWER(u.lastname) LIKE :seller_term)'''
        params['seller_term'] = f'%{seller_search_term}%'
    
    # Add ordering and limit for top K
    if top_k and top_k.isdigit():
        query += ' ORDER BY p.price DESC LIMIT :top_k'
        params['top_k'] = int(top_k)
    else:
        query += ' ORDER BY p.productid'

    # wrap result in subquery for order_by
    if order_by == 'rating':
        query = f"SELECT * FROM ({query}) AS p JOIN (SELECT productid, AVG(rating) AS avg_rating FROM ProductReviews GROUP BY productid) AS pr ON p.productid = pr.productid ORDER BY pr.avg_rating DESC"
    elif order_by == 'sales':
        query = f"SELECT * FROM ({query}) AS p JOIN (SELECT productid, COUNT(*) AS sales FROM Purchases GROUP BY productid) AS o ON p.productid = o.productid ORDER BY o.sales DESC"

    print('Final query:', query)
    # Execute the query
    products = app.db.execute(query, **params)
    
    # Convert to list of dictionaries with all needed product information
    product_list = [
        {
            "id": product.productid,
            "name": product.prodname,
            "price": float(product.price),
            "description": product.description,
            "quantity": product.quantity,
            "seller_name": f"{product.firstname} {product.lastname}"
        }
        for product in products
    ]
    
    return jsonify(product_list)

@bp.route('/manage_inventory')
@login_required
def manage_inventory():
    form = ProductForm() #initialize form
    # Fetch the products for the logged-in seller
    products = app.db.execute("""
        SELECT productid, prodname, price, quantity, description, imagepath, category FROM Products
        WHERE sellerid = :sellerid
    """, sellerid=current_user.userid)

    return render_template('manage_inventory.html', form=form, products=products)