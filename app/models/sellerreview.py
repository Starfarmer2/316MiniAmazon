from flask import current_app as app


class SellerReview:
    def __init__(self, buyerid, sellerid, dtime, rating, review): 
        self.buyerid = buyerid 
        self.sellerid = sellerid 
        self.dtime = dtime 
        self.rating = rating 
        self.review = review 


