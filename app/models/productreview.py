from flask import current_app as app


class ProductReview:
    def __init__(self, productid, buyerid, dtime, review, rating): 
        self.productid = productid
        self.buyerid = buyerid
        self.dtime = dtime 
        self.review = review 
        self.rating = rating 

