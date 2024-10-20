from flask import current_app as app
from datetime import datetime

class Purchase:
    def __init__(self, productid, userid, dtime, quantity, status, price, prodname):
        self.productid = productid
        self.userid = userid
        self.dtime = dtime
        self.quantity = quantity
        self.status = status
        self.price = price
        self.prodname = prodname

    @staticmethod
    def create(productid, userid, dtime, quantity):
        try:
            app.db.execute('''
INSERT INTO Purchases(productid, userid, dtime, quantity, status)
VALUES(:productid, :userid, :dtime, :quantity, TRUE)
''', productid=productid, userid=userid, dtime=dtime, quantity=quantity)
            return True
        except Exception as e:
            print(f"Error creating purchase: {e}")
            return False

    @staticmethod
    def get_by_time(userid, purchase_time):
        rows = app.db.execute('''
SELECT p.productid, p.userid, p.dtime, p.quantity, p.status, pr.price, pr.prodname
FROM Purchases p
JOIN Products pr ON p.productid = pr.productid
WHERE p.userid = :userid AND p.dtime = :purchase_time
''', userid=userid, purchase_time=purchase_time)
        return [Purchase(*row) for row in rows]
