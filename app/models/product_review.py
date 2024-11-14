from flask import current_app as app

class ProductReview:
    def __init__(self, productid, buyerid, dtime, review, rating, helpedcount=0, helped_by=None):
        self.productid = productid
        self.buyerid = buyerid
        self.dtime = dtime
        self.review = review
        self.rating = rating
        self.helpedcount = helpedcount
        self.helped_by = helped_by or []

    @staticmethod
    def get_by_product(productid):
        # First get top 3 most helped reviews
        top_helpful = app.db.execute('''
        SELECT pr.productid, pr.buyerid, pr.dtime, pr.review, pr.rating, pr.helpedcount
        FROM ProductReviews pr
        WHERE pr.productid = :productid
        ORDER BY pr.helpedcount DESC
        LIMIT 3
        ''', productid=productid)

        # Then get remaining reviews sorted by date
        remaining = app.db.execute('''
        SELECT pr.productid, pr.buyerid, pr.dtime, pr.review, pr.rating, pr.helpedcount
        FROM ProductReviews pr
        WHERE pr.productid = :productid
        AND (pr.productid, pr.buyerid) NOT IN (
            SELECT productid, buyerid
            FROM ProductReviews
            WHERE productid = :productid
            ORDER BY helpedcount DESC
            LIMIT 3
        )
        ORDER BY pr.dtime DESC
        ''', productid=productid)

        # Combine both results
        return [ProductReview(*row) for row in top_helpful] + [ProductReview(*row) for row in remaining]

    @staticmethod
    def mark_helpful(productid, buyerid, voter_id):
        try:
            rows = app.db.execute('''
            UPDATE ProductReviews
            SET helpedcount = helpedcount + 1,
                helped_by = array_append(helped_by, :voter_id)
            WHERE productid = :productid 
            AND buyerid = :buyerid
            AND NOT (:voter_id = ANY(helped_by))
            AND buyerid != :voter_id
            RETURNING helpedcount
            ''', productid=productid, buyerid=buyerid, voter_id=voter_id)
            
            return rows[0][0] if rows else None
        except Exception as e:
            app.logger.error(f"Error marking review as helpful: {e}")
            return None

    @staticmethod
    def unmark_helpful(productid, buyerid, voter_id):
        try:
            rows = app.db.execute('''
            UPDATE ProductReviews
            SET helpedcount = helpedcount - 1,
                helped_by = array_remove(helped_by, :voter_id)
            WHERE productid = :productid 
            AND buyerid = :buyerid
            AND :voter_id = ANY(helped_by)
            RETURNING helpedcount
            ''', productid=productid, buyerid=buyerid, voter_id=voter_id)
            
            return rows[0][0] if rows else None
        except Exception as e:
            app.logger.error(f"Error unmarking review as helpful: {e}")
            return None

    @staticmethod
    def is_marked_helpful(productid, buyerid, voter_id):
        rows = app.db.execute('''
        SELECT :voter_id = ANY(helped_by)
        FROM ProductReviews
        WHERE productid = :productid AND buyerid = :buyerid
        ''', productid=productid, buyerid=buyerid, voter_id=voter_id)
        return rows[0][0] if rows else False

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

