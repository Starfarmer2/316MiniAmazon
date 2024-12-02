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


@bp.route('/order_fulfillment', methods=['GET'])
@login_required
def order_fulfillment():
    #renders the Order Fulfillment page for sellers.
    
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').lower()  # 'true', 'false', or ''
    
    #sQL fetch orders related to the current seller
    base_query = """
        SELECT p.productid, p.userid AS buyer_id, p.dtime, p.quantity, p.status,
               u.firstname || ' ' || u.lastname AS buyer_name, u.address, pr.prodname
        FROM Purchases p
        JOIN Products pr ON p.productid = pr.productid
        JOIN Users u ON p.userid = u.userid
        WHERE pr.sellerid = :seller_id
    """
    params = {'seller_id': current_user.userid}
    
    #search and filter conditions
    if search_query:
        base_query += """
            AND (u.firstname || ' ' || u.lastname ILIKE :search
                 OR u.address ILIKE :search
                 OR pr.prodname ILIKE :search)
        """
        params['search'] = f"%{search_query}%"
    
    if status_filter in ['true', 'false']:
        base_query += " AND p.status = :status"
        params['status'] = (status_filter == 'true')  #string to boolean
    
    #dd reverse chronological order
    base_query += " ORDER BY p.dtime DESC"
    
    orders = app.db.execute(base_query, **params)

    order_list = []
    for order in orders:
        order_list.append({
            'productid': order.productid,
            'buyer_id': order.buyer_id,
            'dtime': order.dtime,
            'quantity': order.quantity,
            'status': order.status,
            'buyer_name': order.buyer_name,
            'address': order.address,
            'prodname': order.prodname,
        })
    
    return render_template('order_fulfillment.html', orders=order_list)


@bp.route('/order_fulfillment/mark_fulfilled/<int:product_id>/<int:buyer_id>/<string:dtime>', methods=['POST'])
@login_required
def mark_fulfilled(product_id, buyer_id, dtime):
    """
    Handle marking an order item as fulfilled.
    """
    # Placeholder for actual implementation
    flash(f"Order with product ID {product_id} for buyer ID {buyer_id} has been marked as fulfilled.")
    return redirect(url_for('orders.order_fulfillment'))
