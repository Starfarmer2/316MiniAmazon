from flask import current_app as app

class ProductReview:
    def __init__(self, productid, buyerid, dtime, review, rating, helpedcount=0):
        self.productid = productid
        self.buyerid = buyerid
        self.dtime = dtime
        self.review = review
        self.rating = rating
        self.helpedcount = helpedcount

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
            # First check if this user has already marked this product as helpful
            exists = app.db.execute('''
            SELECT 1 FROM Helped
            WHERE productid = :productid AND userid = :voter_id
            ''', productid=productid, voter_id=voter_id)
            
            if exists:
                return None  # User already marked this as helpful
                
            # Add to Helped table
            app.db.execute('''
            INSERT INTO Helped(productid, userid)
            VALUES(:productid, :voter_id)
            ''', productid=productid, voter_id=voter_id)
            
            # Update helpedcount
            rows = app.db.execute('''
            UPDATE ProductReviews
            SET helpedcount = helpedcount + 1
            WHERE productid = :productid AND buyerid = :buyerid
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
            # Remove from Helped table
            app.db.execute('''
            DELETE FROM Helped
            WHERE productid = :productid AND userid = :voter_id
            ''', productid=productid, voter_id=voter_id)
            
            # Update helpedcount
            rows = app.db.execute('''
            UPDATE ProductReviews
            SET helpedcount = helpedcount - 1
            WHERE productid = :productid AND buyerid = :buyerid
            AND helpedcount > 0
            RETURNING helpedcount
            ''', productid=productid, buyerid=buyerid)
            
            return rows[0][0] if rows else None
        except Exception as e:
            app.logger.error(f"Error unmarking review as helpful: {e}")
            return None

    @staticmethod
    def is_marked_helpful(productid, buyerid, voter_id):
        rows = app.db.execute('''
        SELECT 1 FROM Helped
        WHERE productid = :productid AND userid = :voter_id
        ''', productid=productid, voter_id=voter_id)
        return bool(rows)

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
