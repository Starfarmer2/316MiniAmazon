from flask import current_app as app

class SellerReview:
    def __init__(self, buyerid, sellerid, dtime, rating, review): 
        self.buyerid = buyerid 
        self.sellerid = sellerid 
        self.dtime = dtime 
        self.rating = rating 
        self.review = review

    @staticmethod
    def get_most_recent_by_user(user_id):
        rows = app.db.execute('''
        SELECT buyerid, sellerid, dtime, rating, review
        FROM SellerReviews
        WHERE buyerid = :user_id
        ORDER BY dtime DESC
        LIMIT 1
        ''', user_id=user_id)
        return SellerReview(*rows[0]) if rows else None

    @staticmethod
    def get_recent_by_user(user_id, limit=5):
        rows = app.db.execute('''
        SELECT buyerid, sellerid, dtime, rating, review
        FROM SellerReviews
        WHERE buyerid = :user_id
        ORDER BY dtime DESC
        LIMIT :limit
        ''', user_id=user_id, limit=limit)
        return [SellerReview(*row) for row in rows]
