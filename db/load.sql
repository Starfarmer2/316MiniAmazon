\COPY Users FROM 'User1.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.users_userid_seq',
                         (SELECT MAX(userid)+1 FROM Users),
                         false);

\COPY Sellers FROM 'Seller1.csv' WITH DELIMITER ',' NULL '' CSV

\COPY Products FROM 'Product1.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.products_productid_seq',
                         (SELECT MAX(productid)+1 FROM Products),
                         false);

\COPY Carts FROM 'Cart1.csv' WITH DELIMITER ',' NULL '' CSV

\COPY Purchases FROM 'Purchase1.csv' WITH DELIMITER ',' NULL '' CSV

\COPY ProductReviews FROM 'ProductReview1.csv' WITH DELIMITER ',' NULL '' CSV

\COPY SellerReviews FROM 'SellerReview1.csv' WITH DELIMITER ',' NULL '' CSV

\COPY MarkedProductReviewHelpful FROM 'MarkedProductReviewHelpful1.csv' WITH DELIMITER ',' NULL '' CSV
SELECT setval('productreviews_reviewid_seq', (SELECT MAX(reviewid) FROM ProductReviews));

\COPY MarkedSellerReviewHelpful FROM 'MarkedSellerReviewHelpful1.csv' WITH DELIMITER ',' NULL '' CSV
SELECT setval('sellerreviews_reviewid_seq', (SELECT MAX(reviewid) FROM SellerReviews));
