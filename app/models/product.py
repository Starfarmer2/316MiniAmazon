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
    def add_product(prodname, price, quantity, description, sellerid, imagepath="NoImage", category="NoCategory"):
        if not imagepath:
            imagepath = "NoImage"
        if not category:
            category = "NoCategory"
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
            app.logger.debug(f"Product added with ID: {productid}")
            return Product.get(productid)
        except Exception as e:
            # handle the exception, possibly log it
            print(f"Error adding product: {e}")
            return None

    @staticmethod
    def update_product(productid, prodname, price, quantity, description, imagepath="NoImage", category="NoCategory"):
        if not imagepath:
            imagepath = "NoImage"
        if not category:
            category = "NoCategory"
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
            #handle the exception, log it
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

    #Not in use currently
    @staticmethod
    def filter_by_name(query):
        rows = app.db.execute("""
        SELECT productid, sellerid, prodname, description, 
               imagepath, price, quantity, category
        FROM Products
        WHERE quantity > 0 
          AND (LOWER(prodname) LIKE LOWER(:query)) 
        """,
                              query=f'%{query}%')
        return [Product(*row) for row in rows]

    @staticmethod
    def filter_by_seller(seller_search_term):
        # Check if the seller_search_term is numeric
        is_numeric = seller_search_term.isdigit()
        
        # Prepare the SQL query
        query = """
        SELECT p.productid, p.sellerid, p.prodname, p.description, 
            p.imagepath, p.price, p.quantity, p.category
        FROM Products p
        JOIN Sellers s ON p.sellerid = s.userid
        WHERE p.quantity > 0 
        AND (
            LOWER(s.firstname) LIKE LOWER(:name_search_term) 
            OR LOWER(s.lastname) LIKE LOWER(:name_search_term)
        """
        
        # Add condition for seller ID if the search term is numeric
        if is_numeric:
            query += " OR s.userid = :seller_id"
        
        query += ")"

        # Execute the query
        rows = app.db.execute(query, 
                            name_search_term=f'%{seller_search_term}%',  # For name matching
                            seller_id=seller_search_term if is_numeric else None)  # Use the raw term for ID comparison

        return [Product(*row) for row in rows]

