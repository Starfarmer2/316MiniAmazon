from flask import current_app as app


class Seller:
    def __init__(self, userid, email, name, address, password, balance): 
        self.userid = userid 
        self.email = email 
        self.name = name 
        self.address = address 
        self.password = password
        self.balance = balance

