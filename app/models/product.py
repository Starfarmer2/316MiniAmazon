from flask import current_app as app

class Product:
    def __init__(self, productid, sellerid, prodname, description, 
                 imagepath, price, quantity, category):
        self.productid = productid
        self.sellerid = sellerid 
        self.prodname = prodname 
        self.description = description 
        self.imagepath = imagepath 
        self.price = price 
        self.quantity = quantity
        self.category = category

    @staticmethod
    def get(productid):
        rows = app.db.execute('''
        SELECT productid, sellerid, prodname, description, 
               imagepath, price, quantity, category
        FROM Products
        WHERE productid = :productid
        ''',
                              productid=productid)
        return Product(*(rows[0])) if rows else None

    @staticmethod
    def get_all():
        rows = app.db.execute('''
        SELECT productid, sellerid, prodname, description, 
               imagepath, price, quantity, category
        FROM Products
        WHERE quantity > 0
        ''')
        return [Product(*row) for row in rows]

    @staticmethod
    def add_product(prodname, price, quantity, description, sellerid, imagepath=None, category=None):
        try:
            rows = app.db.execute("""
            INSERT INTO Products(sellerid, prodname, description, imagepath, price, quantity, category)
            VALUES(:sellerid, :prodname, :description, :imagepath, :price, :quantity, :category)
            RETURNING productid
            """,
                                  sellerid=sellerid,
                                  prodname=prodname,
                                  description=description,
                                  imagepath=imagepath,
                                  price=price,
                                  quantity=quantity,
                                  category=category)
            productid = rows[0][0]
            return Product.get(productid)
        except Exception as e:
            # handle the exception, possibly log it
            print(f"Error adding product: {e}")
            return None

    @staticmethod
    def update_product(productid, prodname, price, quantity, description, imagepath=None, category=None):
        try:
            app.db.execute("""
            UPDATE Products
            SET prodname = :prodname, 
                description = :description, 
                imagepath = :imagepath, 
                price = :price, 
                quantity = :quantity, 
                category = :category
            WHERE productid = :productid
            """,
                       productid=productid,
                       prodname=prodname,
                       description=description,
                       imagepath=imagepath,
                       price=price,
                       quantity=quantity,
                       category=category)
            return Product.get(productid)
        except Exception as e:
            # handle the exception, possibly log it
            print(f"Error updating product: {e}")
            return None

    @staticmethod
    def delete_product(productid):
        try:
            app.db.execute("""
            DELETE FROM Products
            WHERE productid = :productid
            """,
                           productid=productid)
            return True
        except Exception as e:
            # handle the exception, possibly log it
            print(f"Error deleting product: {e}")
            return False

    @staticmethod
    def search(query):
        rows = app.db.execute("""
        SELECT productid, sellerid, prodname, description, 
               imagepath, price, quantity, category
        FROM Products
        WHERE quantity > 0 
          AND (LOWER(prodname) LIKE LOWER(:query) 
               OR LOWER(description) LIKE LOWER(:query)
               OR LOWER(category) LIKE LOWER(:query))
        """,
                              query=f'%{query}%')
        return [Product(*row) for row in rows]
