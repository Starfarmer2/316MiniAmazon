from flask import current_app as app

class ProductReview:
    def __init__(self, productid, buyerid, dtime, review, rating):
        self.productid = productid
        self.buyerid = buyerid
        self.dtime = dtime
        self.review = review
        self.rating = rating

    @staticmethod
    def get_by_product(productid):
        rows = app.db.execute('''
        SELECT productid, buyerid, dtime, review, rating
        FROM ProductReviews
        WHERE productid = :productid
        ORDER BY dtime DESC
        ''', productid=productid)
        return [ProductReview(*row) for row in rows]
