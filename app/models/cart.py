from flask import current_app as app

class Cart:
    def __init__(self, userid, productid, productname, quantity, unit_price):
        self.userid = userid
        self.productid = productid
        self.productname = productname
        self.quantity = quantity
        self.unit_price = unit_price

    @staticmethod
    def get_user_cart(userid):
        rows = app.db.execute('''
        SELECT userid, productid, productname, quantity, unit_price
        FROM Carts
        WHERE userid = :userid
        ''', userid=userid)
        return [Cart(*row) for row in rows]

    @staticmethod
    def get_item(userid, productid):
        rows = app.db.execute('''
        SELECT userid, productid, productname, quantity, unit_price
        FROM Carts
        WHERE userid = :userid AND productid = :productid
        ''', userid=userid, productid=productid)
        return Cart(*rows[0]) if rows else None

    @staticmethod
    def add_item(userid, productid, productname, quantity, unit_price):
        try:
            app.db.execute('''
            INSERT INTO Carts (userid, productid, productname, quantity, unit_price)
            VALUES (:userid, :productid, :productname, :quantity, :unit_price)
            ON CONFLICT (userid, productid) DO UPDATE
            SET quantity = Carts.quantity + :quantity
            ''', userid=userid, productid=productid, productname=productname, quantity=quantity, unit_price=unit_price)
            return True
        except Exception as e:
            print(f"Error adding item to cart: {e}")
            return False

    @staticmethod
    def remove_item(userid, productid):
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
        try:
            app.db.execute('''
            DELETE FROM Carts
            WHERE userid = :userid
            ''', userid=userid)
            return True
        except Exception as e:
            print(f"Error clearing cart: {e}")
            return False

    @staticmethod
    def get_cart_total(userid):
        total = app.db.execute('''
        SELECT SUM(quantity * unit_price)
        FROM Carts
        WHERE userid = :userid
        ''', userid=userid)
        return total[0][0] if total and total[0][0] else 0
