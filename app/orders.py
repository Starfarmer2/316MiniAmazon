from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from .models.cart import Cart
from .models.purchase import Purchase
from datetime import datetime

bp = Blueprint('orders', __name__)

@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = Cart.get_user_cart(current_user.userid)
    if not cart_items:
        flash('Your cart is empty.')
        return redirect(url_for('cart.view_cart'))
    
    if request.method == 'POST':
        print('POST request received')  # Debugging line to check if POST request is received
        all_purchases_successful = True
        
        # Loop through cart items to process purchases
        for item in cart_items:
            print(f'Processing purchase for product {item.productname} with quantity {item.quantity}')
            purchase, message = Purchase.create_purchase(current_user.userid, item.productid, item.quantity)
            
            # Handle error during purchase
            if not purchase:
                flash(f'Error purchasing {item.productname}: {message}')
                all_purchases_successful = False
                break
        
        # If all purchases are successful, clear the cart and redirect to purchase history
        if all_purchases_successful:
            print('All purchases successful')  # Debugging line
            Cart.clear_cart(current_user.userid)
            flash('All items purchased successfully!')
            return redirect(url_for('users.user_purchases', user_id=current_user.userid))
        else:
            flash('There was an error processing your order. Please try again.')

    total = sum(item.unit_price * item.quantity for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)



@bp.route('/order_confirmation/<purchase_time>')
@login_required
def order_confirmation(purchase_time):
    purchases = Purchase.get_by_time(current_user.userid, purchase_time)
    if not purchases:
        flash('Order not found.')
        return redirect(url_for('index.index'))
    
    # We need to fetch product details separately since Purchase doesn't include price and name
    from .models.product import Product
    purchase_details = []
    total = 0
    for purchase in purchases:
        product = Product.get(purchase.pid)
        if product:
            subtotal = product.price * purchase.quantity
            total += subtotal
            purchase_details.append({
                'prodname': product.prodname,
                'quantity': purchase.quantity,
                'price': product.price,
                'subtotal': subtotal
            })
    
    return render_template('order_confirmation.html', 
                           purchases=purchase_details, 
                           total=total, 
                           purchase_time=purchase_time)
