from flask import Blueprint, redirect, url_for, flash, request, render_template
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
    
    success = Cart.add_item(current_user.userid, product_id, product.prodname, quantity, product.price)
    if success:
        flash('Item added to cart successfully.')
    else:
        flash('Error adding item to cart.')
    
    return redirect(url_for('products.product_detail', product_id=product_id))

@bp.route('/remove_from_cart/<int:productid>', methods=['POST'])
@login_required
def remove_from_cart(productid):
    success = Cart.remove_item(current_user.userid, productid)
    if success:
        flash('Item removed from cart successfully.')
    else:
        flash('Error removing item from cart.')
    return redirect(url_for('cart.view_cart'))

@bp.route('/view_cart')
@login_required
def view_cart():
    cart_items = Cart.get_user_cart(current_user.userid)
    total = Cart.get_cart_total(current_user.userid)
    return render_template('cart.html', cart_items=cart_items, total=total)

@bp.route('/update_cart_item/<int:productid>', methods=['POST'])
@login_required
def update_cart_item(productid):
    quantity = int(request.form.get('quantity', 1))
    success = Cart.update_item(current_user.userid, productid, quantity)
    if success:
        flash('Cart updated successfully.')
    else:
        flash('Error updating cart.')
    return redirect(url_for('cart.view_cart'))

@bp.route('/clear_cart', methods=['POST'])
@login_required
def clear_cart():
    success = Cart.clear_cart(current_user.userid)
    if success:
        flash('Cart cleared successfully.')
    else:
        flash('Error clearing cart.')
    return redirect(url_for('cart.view_cart'))
