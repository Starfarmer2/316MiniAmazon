from flask import current_app as app

class Cart:
    def __init__(self, userid, productid, productname, quantity, unit_price, status='in_cart'):
        self.userid = userid
        self.productid = productid
        self.productname = productname
        self.quantity = quantity
        self.unit_price = unit_price
        self.status = status

    @staticmethod
    def get_user_cart(userid, status='in_cart'):
        # Fetch items based on the status (either 'in_cart' or 'saved')
        rows = app.db.execute('''
        SELECT userid, productid, productname, quantity, unit_price, status
        FROM Carts
        WHERE userid = :userid AND status = :status
        ''', userid=userid, status=status)
        return [Cart(*row) for row in rows]

    @staticmethod
    def get_item(userid, productid):
        # Fetch a specific item by user ID and product ID
        rows = app.db.execute('''
        SELECT userid, productid, productname, quantity, unit_price, status
        FROM Carts
        WHERE userid = :userid AND productid = :productid
        ''', userid=userid, productid=productid)
        return Cart(*rows[0]) if rows else None

    @staticmethod
    def add_item(userid, productid, productname, quantity, unit_price, status='in_cart'):
        # Add an item with a specific status (default to 'in_cart')
        try:
            app.db.execute('''
            INSERT INTO Carts (userid, productid, productname, quantity, unit_price, status)
            VALUES (:userid, :productid, :productname, :quantity, :unit_price, :status)
            ON CONFLICT (userid, productid) DO UPDATE
            SET quantity = Carts.quantity + :quantity, status = :status
            ''', userid=userid, productid=productid, productname=productname, quantity=quantity, unit_price=unit_price, status=status)
            return True
        except Exception as e:
            print(f"Error adding item to cart: {e}")
            return False

    @staticmethod
    def update_item_status(userid, productid, status):
        # Update the status of an item (e.g., move from 'in_cart' to 'saved' or vice versa)
        try:
            app.db.execute('''
            UPDATE Carts
            SET status = :status
            WHERE userid = :userid AND productid = :productid
            ''', userid=userid, productid=productid, status=status)
            return True
        except Exception as e:
            print(f"Error updating item status: {e}")
            return False

    @staticmethod
    def remove_item(userid, productid):
        # Remove an item from the cart
        try:
            app.db.execute('''
            DELETE FROM Carts
            WHERE userid = :userid AND productid = :productid
            ''', userid=userid, productid=productid)
            return True
        except Exception as e:
            print(f"Error removing item from cart: {e}")
            return False

    @staticmethod
    def update_item(userid, productid, quantity):
        # Update the quantity of a specific item
        try:
            app.db.execute('''
            UPDATE Carts
            SET quantity = :quantity
            WHERE userid = :userid AND productid = :productid
            ''', userid=userid, productid=productid, quantity=quantity)
            return True
        except Exception as e:
            print(f"Error updating cart item: {e}")
            return False

    @staticmethod
    def clear_cart(userid):
        # Clear all items with status 'in_cart' (leave saved items)
        try:
            app.db.execute('''
            DELETE FROM Carts
            WHERE userid = :userid AND status = 'in_cart'
            ''', userid=userid)
            return True
        except Exception as e:
            print(f"Error clearing cart: {e}")
            return False

    @staticmethod
    def get_cart_total(userid, status='in_cart'):
        # Calculate the total only for items that are 'in_cart'
        total = app.db.execute('''
        SELECT SUM(quantity * unit_price)
        FROM Carts
        WHERE userid = :userid AND status = :status
        ''', userid=userid, status=status)
        return total[0][0] if total and total[0][0] else 0
