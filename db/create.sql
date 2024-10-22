CREATE TABLE Users (
  userid INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, 
  email VARCHAR(96) UNIQUE,  -- check if valid address
  firstname VARCHAR(96) NOT NULL, 
  lastname VARCHAR(96) NOT NULL, 
  address VARCHAR(255), 
  password VARCHAR(255) NOT NULL, 
  balance FLOAT NOT NULL CHECK(balance >= 0)
);

CREATE TABLE Sellers (
  userid INT PRIMARY KEY REFERENCES Users(userid), 
  email VARCHAR(96) UNIQUE, 
  firstname VARCHAR(96) NOT NULL, 
  lastname VARCHAR(96) NOT NULL, 
  address VARCHAR(255), 
  password CHAR(255) NOT NULL, 
  balance FLOAT NOT NULL CHECK(balance >= 0)
);

CREATE TABLE Products (
  productid INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, 
  sellerid INT NOT NULL, 
  prodname VARCHAR(255), 
  description VARCHAR(255) NOT NULL, 
  imagepath VARCHAR(255) NOT NULL, 
  price FLOAT NOT NULL, 
  quantity INT NOT NULL CHECK(quantity >= 0),
  category VARCHAR(48) NOT NULL -- in predefined categories
);

CREATE TABLE Carts (
  userid INT, 
  productid INT REFERENCES Products(productid), 
  productname VARCHAR(255), 
  quantity INT CHECK(quantity > 0), 
  unit_price FLOAT, 
  PRIMARY KEY (userid, productid)
);

CREATE TABLE Purchases (
  productid INT NOT NULL, 
  userid INT NOT NULL, 
  dtime TIMESTAMP, 
  quantity INT NOT NULL CHECK (quantity > 0),
  status BOOLEAN, 
  PRIMARY KEY (productid, userid, dtime)
);

CREATE TABLE ProductReviews (
  productid INT REFERENCES Products(productid), 
  buyerid INT REFERENCES Users(userid), 
  dtime TIMESTAMP, 
  review VARCHAR(255), 
  rating INT NOT NULL CHECK(rating > 0 AND rating <= 5), 
  PRIMARY KEY (productid, buyerid)
);

CREATE TABLE SellerReviews (
  buyerid INT NOT NULL, 
  sellerid INT NOT NULL, 
  dtime timestamp NOT NULL, 
  rating INT NOT NULL CHECK(rating > 0 AND rating <= 5), 
  review VARCHAR(255),
  PRIMARY KEY (sellerid, buyerid)
);