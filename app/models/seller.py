from flask import current_app as app


class Seller:
    def __init__(self, userid, email, name, address, password, balance): 
        self.userid = userid 
        self.email = email 
        self.name = name 
        self.address = address 
        self.password = password
        self.balance = balance

    @staticmethod
    def get_seller_products(sellerid):
        try:
            rows = app.db.execute('''
            SELECT ProductID, SellerID, ProdName, Description, Image_Path, Price, Quantity, Category
            FROM Product
            WHERE SellerID = :sellerid
            ''', sellerid=sellerid)
            return [row for row in rows]

        except Exception as e:
            print(f"Error finding seller's products: {e}")
            return False