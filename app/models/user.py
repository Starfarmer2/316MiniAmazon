from flask_login import UserMixin
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash

from .. import login


class User(UserMixin):
    def __init__(self, userid, email, firstname, lastname, address, balance):
        self.id = userid
        self.userid = userid
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.address = address
        self.balance = balance

    def save(self):
        app.db.execute("""
        UPDATE Users
        SET email = :email, 
            firstname = :firstname, 
            lastname = :lastname, 
            address = :address, 
            balance = :balance
        WHERE userid = :userid
        """, 
        email=self.email,
        firstname=self.firstname,
        lastname=self.lastname,
        address=self.address,
        balance=self.balance,
        userid=self.userid)

    @staticmethod
    def get_by_auth(email, password):
        rows = app.db.execute("""
        SELECT password, userid, email, firstname, lastname, address, balance
        FROM Users
        WHERE email = :email
        """, email=email)
        if not rows:  # email not found
            return None
        elif not check_password_hash(rows[0][0], password):
            # incorrect password
            return None
        else:
            return User(*(rows[0][1:]))

    @staticmethod
    def email_exists(email):
        rows = app.db.execute("""
        SELECT email
        FROM Users
        WHERE email = :email
        """, email=email)
        return len(rows) > 0

    @staticmethod
    def register(email, password, firstname, lastname):
        try:
            rows = app.db.execute("""
            INSERT INTO Users(email, firstname, lastname, address, password, balance)
            VALUES(:email, :firstname, :lastname, NULL, :password, 0)
            RETURNING userid
            """,
              email=email,
              password=generate_password_hash(password),
              firstname=firstname, lastname=lastname)
            id = rows[0][0]
            return User.get(id)
        except Exception as e:
            # likely email already in use; better error checking and reporting needed;
            # the following simply prints the error to the console:
            print(str(e))
            return None

    @staticmethod
    @login.user_loader
    def get(userid):
        rows = app.db.execute("""
        SELECT userid, email, firstname, lastname, address, balance
        FROM Users
        WHERE userid = :userid
        """, userid=userid)
        return User(*(rows[0])) if rows else None
    
    @staticmethod
    def get_purchases(user_id):
        rows = app.db.execute("""
        SELECT p.prodname, pr.dtime
        FROM Purchases pr
        JOIN Products p ON pr.productid = p.productid
        WHERE pr.userid = :user_id
        ORDER BY pr.dtime DESC
        """, user_id=user_id)

        return rows if rows else None

    # add a product to cart 
    # remove a product from cart 
    # write/update a review about a product 
    # remove a review about a product 
    # write/update a review about a seller 
    # remove a review about a seller 
    # buy all products in cart 
    # sell a product 

    @staticmethod 
    def get_balance(userid):
        curr_balance = app.db.execute("""
        SELECT balance 
        FROM Users 
        WHERE userid = :userid
        """,
        userid=userid)

        return curr_balance

    @staticmethod 
    def deposit_balance(userid, amount): 
        app.db.execute("""
        UPDATE Users 
        SET balance = balance + :amount 
        WHERE userid = :userid
        """,
        userid=userid, amount=amount)

    @staticmethod 
    def withdraw_balance(userid, amount): 
        app.db.execute("""
        UPDATE Users 
        SET balance = balance - :amount 
        WHERE userid = :userid AND balance >= :amount
        """,
        userid=userid, amount=amount)


    @staticmethod
    def add_product_to_cart(productid): 
        pass 


    def is_seller(self):
        rows = app.db.execute("""
            SELECT UserID FROM Sellers
            WHERE UserID = :userid
        """, userid=self.userid)
        return len(rows) > 0  # Returns True if the user is a seller