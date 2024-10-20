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

    @staticmethod
    def get_most_recent_by_user(user_id):
        rows = app.db.execute('''
        SELECT productid, buyerid, dtime, review, rating
        FROM ProductReviews
        WHERE buyerid = :user_id
        ORDER BY dtime DESC
        LIMIT 1
        ''', user_id=user_id)
        return ProductReview(*rows[0]) if rows else None

    @staticmethod
    def get_recent_by_user(user_id, limit=5):
        rows = app.db.execute('''
        SELECT productid, buyerid, dtime, review, rating
        FROM ProductReviews
        WHERE buyerid = :user_id
        ORDER BY dtime DESC
        LIMIT :limit
        ''', user_id=user_id, limit=limit)
        return [ProductReview(*row) for row in rows]
