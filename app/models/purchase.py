from flask import current_app as app
from datetime import datetime

class Purchase:
    def __init__(self, productid, userid, dtime, quantity, status):
        self.productid = productid
        self.userid = userid
        self.dtime = dtime
        self.quantity = quantity
        self.status = status

    @staticmethod
    def create_purchase(userid, productid, quantity):
        try:
            # Get user's balance
            print(f"Fetching balance for user {userid}")
            user_balance_row = app.db.execute(
                'SELECT balance FROM Users WHERE userid = :userid',
                userid=userid  # Passing parameters directly
            )
            if not user_balance_row:
                print("User not found")
                return None, "User not found"
            user_balance = user_balance_row[0][0]
            print(f"User balance: {user_balance}")

            # Get product details and the seller ID
            print(f"Fetching product details for product {productid}")
            product_row = app.db.execute(
                'SELECT price, quantity, sellerid FROM Products WHERE productid = :productid',
                productid=productid  # Passing parameters directly
            )
            if not product_row:
                print("Product not found")
                return None, "Product not found"
            product_price, product_quantity, seller_id = product_row[0]
            print(f"Product price: {product_price}, Available quantity: {product_quantity}, Seller id: {seller_id}")

            # Fetch seller's balance
            print(f"Fetching seller's balance for seller {seller_id}")
            seller_balance_row = app.db.execute(
                'SELECT balance FROM Sellers WHERE userid = :seller_id',
                seller_id=seller_id
            )
            if not seller_balance_row:
                print("Seller not found")
                return None, "Seller not found"
            seller_balance = seller_balance_row[0][0]
            print(f"Seller balance: {seller_balance}")

            total_cost = product_price * quantity
            print(f"Total cost for {quantity} units: {total_cost}")

            if user_balance < total_cost:
                print("Insufficient funds")
                return None, "Insufficient funds"

            if product_quantity < quantity:
                print("Insufficient stock")
                return None, "Insufficient stock"

            # Update user's balance
            print(f"Updating user balance, deducting {total_cost}")
            app.db.execute(
                'UPDATE Users SET balance = balance - :amount WHERE userid = :userid',
                amount=total_cost, userid=userid  # Passing parameters directly
            )

            # Update seller's balance
            print(f"Updating seller's balance, adding {total_cost}")
            app.db.execute(
                '''
                BEGIN;
                UPDATE Users SET balance = balance + :amount WHERE userid = :sellerid;
                UPDATE Sellers SET balance = balance + :amount WHERE userid = :sellerid;
                COMMIT;
                ''',
                amount=total_cost, sellerid=seller_id
            )

            # Update product quantity
            print(f"Updating product quantity, reducing by {quantity}")
            app.db.execute(
                'UPDATE Products SET quantity = quantity - :quantity WHERE productid = :productid',
                quantity=quantity, productid=productid  # Passing parameters directly
            )

            # Create purchase record
            print(f"Creating purchase record for user {userid} and product {productid}")
            purchase_row = app.db.execute(
                '''
                INSERT INTO Purchases (productid, userid, dtime, quantity, status)
                VALUES (:productid, :userid, :dtime, :quantity, :status)
                RETURNING productid, userid, dtime, quantity, status
                ''',
                productid=productid, userid=userid, dtime=datetime.now(),
                quantity=quantity, status=False  #Status is false at first, until order is marked fulfulled by seller
            )

            if purchase_row:
                print("Purchase created successfully")
                return Purchase(*purchase_row[0]), "Purchase successful"
            else:
                print("Failed to create purchase record")
                return None, "Failed to create purchase record"

        except Exception as e:
            print(f"Error creating purchase: {e}")
            return None, str(e)



    @staticmethod
    def get(productid, userid, dtime):
        rows = app.db.execute('''
        SELECT productid, userid, dtime, quantity, status
        FROM Purchases
        WHERE productid = :productid AND userid = :userid AND dtime = :dtime
        ''',
                              productid=productid,
                              userid=userid,
                              dtime=dtime)
        return Purchase(*(rows[0])) if rows else None

    @staticmethod
    def get_all_by_uid_since(userid, since):
        rows = app.db.execute('''
        SELECT productid, userid, dtime, quantity, status
        FROM Purchases
        WHERE userid = :userid
        AND dtime >= :since
        ORDER BY dtime DESC
        ''',
                              userid=userid,
                              since=since)
        return [Purchase(*row) for row in rows]

    @staticmethod
    def create(productid, userid, quantity, status=True):
        try:
            rows = app.db.execute('''
            INSERT INTO Purchases(productid, userid, dtime, quantity, status)
            VALUES(:productid, :userid, :dtime, :quantity, :status)
            RETURNING productid, userid, dtime, quantity, status
            ''',
                                  productid=productid,
                                  userid=userid,
                                  dtime=datetime.now(),
                                  quantity=quantity,
                                  status=status)
            return Purchase(*(rows[0])) if rows else None
        except Exception as e:
            print(f"Error creating purchase: {e}")
            return None

    @staticmethod
    def get_by_time(userid, purchase_time):
        rows = app.db.execute('''
        SELECT productid, userid, dtime, quantity, status
        FROM Purchases
        WHERE userid = :userid AND dtime = :purchase_time
        ''', 
                              userid=userid, 
                              purchase_time=purchase_time)
        return [Purchase(*row) for row in rows]

    def save(self):
        app.db.execute('''
        UPDATE Purchases
        SET quantity = :quantity, status = :status
        WHERE productid = :productid AND userid = :userid AND dtime = :dtime
        ''',
                       quantity=self.quantity,
                       status=self.status,
                       productid=self.productid,
                       userid=self.userid,
                       dtime=self.dtime)

    def __repr__(self):
        return f'<Purchase {self.productid}, {self.userid}, {self.dtime}>'
