from flask import Blueprint, jsonify, render_template, send_file, redirect, url_for, flash, request, abort, current_app as app
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from .models.product import Product
from .models.product_review import ProductReview
from .models.user import User
from math import ceil
import os
from datetime import datetime

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
    
    seller = User.get(product.sellerid)
    if seller is None:
        abort(404)
    
    # Get all seller reviews
    all_seller_reviews = app.db.execute('''
        SELECT sr.rating, sr.review, sr.dtime,
               u.firstname, u.lastname,
               sr.buyerid
        FROM SellerReviews sr
        JOIN Users u ON sr.buyerid = u.userid
        WHERE sr.sellerid = :sellerid
        ORDER BY sr.dtime DESC
    ''', sellerid=seller.userid)

    # Format the reviews
    formatted_reviews = []
    for review in all_seller_reviews:
        formatted_reviews.append({
            'rating': review.rating,
            'review': review.review,
            'dtime': review.dtime,
            'reviewer_name': f"{review.firstname} {review.lastname}",
            'buyerid': review.buyerid
        })

    # Get seller review if it exists for current user
    seller_review = None
    has_purchased_from_seller = False
    if current_user.is_authenticated:
        # Check if user has purchased from this seller
        purchase_check = app.db.execute('''
            SELECT COUNT(*) 
            FROM Purchases p
            JOIN Products prod ON p.productid = prod.productid
            WHERE p.userid = :userid AND prod.sellerid = :sellerid
        ''', userid=current_user.userid, sellerid=seller.userid)
        
        has_purchased_from_seller = purchase_check[0][0] > 0 if purchase_check else False

        # Get existing seller review if any
        if has_purchased_from_seller:
            review_check = app.db.execute('''
                SELECT rating, review 
                FROM SellerReviews 
                WHERE buyerid = :buyerid AND sellerid = :sellerid
            ''', buyerid=current_user.userid, sellerid=seller.userid)
            if review_check:
                seller_review = {
                    'rating': review_check[0][0],
                    'review': review_check[0][1]
                }
    # Get reviews with the new sorting logic
    reviews = app.db.execute('''
        WITH TopHelpful AS (
            SELECT pr.productid, pr.buyerid, pr.dtime, pr.review, pr.rating, pr.helpedcount,
                   u.firstname, u.lastname
            FROM ProductReviews pr
            JOIN Users u ON pr.buyerid = u.userid
            WHERE pr.productid = :productid
            ORDER BY pr.helpedcount DESC
            LIMIT 3
        ),
        RemainingReviews AS (
            SELECT pr.productid, pr.buyerid, pr.dtime, pr.review, pr.rating, pr.helpedcount,
                   u.firstname, u.lastname
            FROM ProductReviews pr
            JOIN Users u ON pr.buyerid = u.userid
            WHERE pr.productid = :productid
            AND (pr.productid, pr.buyerid) NOT IN (SELECT productid, buyerid FROM TopHelpful)
            ORDER BY pr.dtime DESC
        )
        SELECT * FROM TopHelpful
        UNION ALL
        SELECT * FROM RemainingReviews
    ''', productid=product_id)
    
    # Check if the current user has purchased this product
    has_purchased = False
    user_review = None
    if current_user.is_authenticated:
        purchase_check = app.db.execute('''
            SELECT COUNT(*)
            FROM Purchases
            WHERE userid = :userid AND productid = :productid
        ''', userid=current_user.userid, productid=product_id)
        has_purchased = purchase_check[0][0] > 0
        
        # Get user's existing review if any
        if has_purchased:
            user_review = app.db.execute('''
                SELECT review, rating
                FROM ProductReviews
                WHERE buyerid = :userid AND productid = :productid
            ''', userid=current_user.userid, productid=product_id)
            user_review = user_review[0] if user_review else None

    return render_template('product_detail.html', 
                         product=product, 
                         seller=seller,
                         seller_review=seller_review, 
                         has_purchased_from_seller=has_purchased_from_seller,
                         reviews=reviews,
                         all_seller_reviews=formatted_reviews,
                         has_purchased=has_purchased,
                         user_review=user_review)

@bp.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_seller():
        flash('You do not have permission to add products.')
        return redirect(url_for('products.manage_inventory'))
    
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

@bp.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    if not request.form.get('rating') or not request.form.get('review'):
        flash('Both rating and review are required.')
        return redirect(url_for('products.product_detail', product_id=product_id))
    
    # Check if user has purchased the product
    rows = app.db.execute('''
        SELECT COUNT(*) 
        FROM Purchases 
        WHERE userid = :userid AND productid = :productid
    ''', userid=current_user.userid, productid=product_id)
    
    has_purchased = rows[0][0] > 0 if rows else False
    
    if not has_purchased:
        flash('You can only review products you have purchased.')
        return redirect(url_for('products.product_detail', product_id=product_id))
    
    try:
        # Check for existing review
        existing_review = app.db.execute('''
            SELECT COUNT(*) 
            FROM ProductReviews 
            WHERE buyerid = :userid AND productid = :productid
        ''', userid=current_user.userid, productid=product_id)
        
        if existing_review and existing_review[0][0] > 0:
            # Update existing review
            app.db.execute('''
                UPDATE ProductReviews 
                SET rating = :rating, review = :review, dtime = :dtime
                WHERE buyerid = :userid AND productid = :productid
            ''', 
                rating=int(request.form['rating']),
                review=request.form['review'],
                dtime=datetime.now(),
                userid=current_user.userid,
                productid=product_id)
            flash('Your review has been updated.')
        else:
            # Create new review
            app.db.execute('''
                INSERT INTO ProductReviews(productid, buyerid, dtime, review, rating, helpedcount, helped_by)
                VALUES(:productid, :userid, :dtime, :review, :rating, 0, ARRAY[]::integer[])
            ''',
                productid=product_id,
                userid=current_user.userid,
                dtime=datetime.now(),
                review=request.form['review'],
                rating=int(request.form['rating']))
            flash('Your review has been added successfully.')
    except Exception as e:
        print(f"Error saving review: {str(e)}")  # For debugging
        flash(f'Error saving review: {str(e)}')
        
    return redirect(url_for('products.product_detail', product_id=product_id))

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

@bp.route('/product_image/<path:filename>')
def serve_product_image(filename):
    """
    Serve product images with graceful fallback to default image when file not found.
    Suppresses file not found errors from logging.
    """
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return send_file(file_path)
    except FileNotFoundError:
        # Instead of raising an error, redirect to a default image
        return redirect(url_for('static', filename='images/no-image-available.png')), 303
    except Exception as e:
        # Log other types of errors that might be important
        app.logger.error(f"Error serving image {filename}: {str(e)}")
        return redirect(url_for('static', filename='images/no-image-available.png')), 303

@bp.route('/filter-products', methods=['POST'])
def filter_products():
    data = request.json
    seller_search_term = data.get('sellerSearchTerm', '').lower()
    product_search_term = data.get('productSearchTerm', '').lower()
    category_search_term = data.get('categorySearchTerm', '').lower()
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

    if category_search_term:
        query += ''' AND (LOWER(p.category) LIKE :category_term)'''
        params['category_term'] = f'%{category_search_term}%'
    
    # Add ordering and limit for top K
    if top_k and top_k.isdigit():
        query += ' ORDER BY p.price DESC LIMIT :top_k'
        params['top_k'] = int(top_k)
    else:
        query += ' ORDER BY p.productid'

    # Wrap result in subquery for avg_rating
    query = f"SELECT p.*, pr.avg_rating FROM ({query}) AS p JOIN (SELECT productid, AVG(rating) AS avg_rating FROM ProductReviews GROUP BY productid) AS pr ON p.productid = pr.productid ORDER BY pr.avg_rating DESC"
    # Wrap result in subquery for order_by
    if order_by == 'sales':
        query = f"SELECT * FROM ({query}) AS p JOIN (SELECT productid, COUNT(*) AS sales FROM Purchases GROUP BY productid) AS o ON p.productid = o.productid ORDER BY o.sales DESC"
    elif order_by == 'quantity':
        query = f"SELECT * FROM ({query}) AS p ORDER BY p.quantity DESC"
    elif order_by == 'rating':
        query = f"SELECT * FROM ({query}) AS p ORDER BY p.avg_rating DESC"
    elif order_by == 'price':
        query = f"SELECT * FROM ({query}) AS p ORDER BY p.price DESC"

    print('Final query:', query)
    # Execute the query
    products = app.db.execute(query, **params)
    
    # Convert to list of dictionaries with all needed product information
    product_list = [
        {
            "id": product.productid,
            "name": product.prodname,
            "imagepath": product.imagepath,
            "price": float(product.price),
            "description": product.description,
            "quantity": product.quantity,
            "seller_name": f"{product.firstname} {product.lastname}",
            "avg_rating": float(product.avg_rating),
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

@bp.route('/mark_helpful', methods=['POST'])
@login_required
def mark_helpful():
    data = request.get_json()
    product_id = data.get('product_id')
    buyer_id = data.get('buyer_id')
    
    if current_user.userid == buyer_id:
        return jsonify({'success': False, 'error': 'Cannot mark your own review as helpful'}), 400

    result = ProductReview.mark_helpful(product_id, buyer_id, current_user.userid)
    
    return jsonify({'success': result is not None})

