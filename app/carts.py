from flask import Blueprint, redirect, url_for, flash, request, render_template, make_response
from flask_login import current_user, login_required
from .models.product import Product
from .models.cart import Cart

bp = Blueprint('cart', __name__)

@bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.get(product_id)
    if not product:
        flash('Product not found.')
        return redirect(url_for('products.all_products'))
    
    quantity = int(request.form.get('quantity', 1))
    if quantity <= 0:
        flash('Invalid quantity.')
        return redirect(url_for('products.product_detail', product_id=product_id))
    
    if product.quantity < quantity: 
        flash('Not enough stock available.')
        return redirect(url_for('products.product_detail', product_id=product_id))
    
    success = Cart.add_item(current_user.userid, product_id, product.prodname, quantity, product.price, status='in_cart')
    if success:
        flash('Item added to cart successfully.')
        pass
    else:
        flash('Error adding item to cart.')
        pass
    
    return redirect(url_for('products.all_products'))

@bp.route('/remove_from_cart/<int:productid>', methods=['POST'])
@login_required
def remove_from_cart(productid):
    success = Cart.remove_item(current_user.userid, productid)
    if success:
        flash('Item removed from cart successfully.')
        pass
    else:
        flash('Error removing item from cart.')
        pass
    return redirect(url_for('cart.view_cart'))

@bp.route('/view_cart')
@login_required
def view_cart():
    # Fetch both "In Cart" and "Saved for Later" items
    cart_items = Cart.get_user_cart(current_user.userid, status='in_cart')
    saved_items = Cart.get_user_cart(current_user.userid, status='saved')
    total = Cart.get_cart_total(current_user.userid, status='in_cart')

    # Render the template and then modify the response headers
    response = make_response(render_template('cart.html', cart_items=cart_items, saved_items=saved_items, total=total))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response

@bp.route('/update_cart_item/<int:productid>', methods=['POST'])
@login_required
def update_cart_item(productid):
    quantity = int(request.form.get('quantity', 1))
    success = Cart.update_item(current_user.userid, productid, quantity)
    if success:
        flash('Cart updated successfully.')
        pass
    else:
        flash('Error updating cart.')
        pass
    return redirect(url_for('cart.view_cart'))

@bp.route('/clear_cart', methods=['POST'])
@login_required
def clear_cart():
    success = Cart.clear_cart(current_user.userid)
    if success:
        flash('Cart cleared successfully.')
        pass
    else:
        flash('Error clearing cart.')
        pass
    return redirect(url_for('cart.view_cart'))

# New route to save an item for later
@bp.route('/save_for_later/<int:product_id>', methods=['POST'])
@login_required
def save_for_later(product_id):
    # Update the item's status to 'saved'
    success = Cart.update_item_status(current_user.userid, product_id, status='saved')
    if success:
        flash('Item saved for later.')
        pass
    else:
        flash('Error saving item for later.')
        pass
    return redirect(url_for('cart.view_cart'))

# New route to move an item back to the cart
@bp.route('/move_to_cart/<int:product_id>', methods=['POST'])
@login_required
def move_to_cart(product_id):
    # Update the item's status to 'in_cart'
    success = Cart.update_item_status(current_user.userid, product_id, status='in_cart')
    if success:
        flash('Item moved back to cart.')
        pass
    else:
        flash('Error moving item back to cart.')
        pass
    return redirect(url_for('cart.view_cart'))
