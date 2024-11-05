from werkzeug.security import generate_password_hash
import csv
from faker import Faker
from datetime import datetime, timedelta
import random

# Configuration
num_users = 100
num_sellers = num_users // 10
num_products = 200
num_purchases = 300
num_product_reviews = 150
num_seller_reviews = 100
num_cart_items = 50

categories = ['personal wellness', 'food', 'athletics']
Faker.seed(0)
fake = Faker()

def get_csv_writer(f):
    return csv.writer(f, dialect='unix')

def gen_users_and_sellers(num_users):
    sellers = []
    with open('User1.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Users...', end=' ', flush=True)
        for uid in range(num_users):
            if uid % 10 == 0:
                print(f'{uid}', end=' ', flush=True)
            profile = fake.profile()
            email = profile['mail']
            address = profile['address']
            plain_password = f'pass{uid}'
            password = generate_password_hash(plain_password)
            firstname, *middle, lastname = profile['name'].split(' ')
            balance = round(random.uniform(0, 1000), 2)
            row = [uid, email, firstname, lastname, address, password, balance]
            if uid < num_sellers:
                sellers.append(row)
            writer.writerow(row)
        print(f'{num_users} users generated')
    
    with open('Sellers.csv', 'w') as f:
        writer = get_csv_writer(f)
        for row in sellers:
            writer.writerow(row)
        print(f'{num_sellers} sellers generated')
    return sellers

def gen_products(num_products, sellers):
    available_pids = []
    with open('Product1.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Products...', end=' ', flush=True)
        for pid in range(num_products):
            if pid % 100 == 0:
                print(f'{pid}', end=' ', flush=True)
            seller = fake.random_element(sellers)
            sellerid = seller[0]
            prodname = fake.sentence(nb_words=4)[:-1]
            description = fake.sentence(nb_words=15)
            imagepath = f"/images/product_{pid}.jpg"
            price = round(random.uniform(1, 500), 2)
            quantity = fake.random_int(min=0, max=50)
            category = fake.random_element(categories)
            writer.writerow([pid, sellerid, prodname, description, imagepath, price, quantity, category])
            available_pids.append(pid)
        print(f'{num_products} products generated')
    return available_pids

def gen_carts(num_cart_items, available_pids):
    with open('Cart1.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Carts...', end=' ', flush=True)
        seen_combinations = set()
        for _ in range(num_cart_items):
            while True:
                userid = fake.random_int(min=0, max=num_users-1)
                productid = fake.random_element(available_pids)
                if (userid, productid) not in seen_combinations:
                    seen_combinations.add((userid, productid))
                    break
            productname = fake.sentence(nb_words=4)[:-1]
            quantity = fake.random_int(min=1, max=5)
            unit_price = round(random.uniform(1, 500), 2)
            writer.writerow([userid, productid, productname, quantity, unit_price])
        print(f'{num_cart_items} cart items generated')

def gen_purchases(num_purchases, available_pids):
    with open('Purchase1.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Purchases...', end=' ', flush=True)
        seen_combinations = set()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        for _ in range(num_purchases):
            while True:
                productid = fake.random_element(available_pids)
                userid = fake.random_int(min=0, max=num_users-1)
                dtime = fake.date_time_between(start_date=start_date, end_date=end_date)
                key = (productid, userid, dtime)
                if key not in seen_combinations:
                    seen_combinations.add(key)
                    break
            
            quantity = fake.random_int(min=1, max=10)
            status = fake.boolean(chance_of_getting_true=90)  # 90% completed purchases
            writer.writerow([productid, userid, dtime, quantity, status])
        print(f'{num_purchases} purchases generated')
    return seen_combinations

def gen_product_reviews(num_reviews, available_pids):
    with open('ProductReview1.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Product Reviews...', end=' ', flush=True)
        seen_combinations = set()
        
        for _ in range(num_reviews):
            while True:
                productid = fake.random_element(available_pids)
                buyerid = fake.random_int(min=0, max=num_users-1)
                if (productid, buyerid) not in seen_combinations:
                    seen_combinations.add((productid, buyerid))
                    break
            
            dtime = fake.date_time_between(start_date='-1y', end_date='now')
            review = fake.paragraph(nb_sentences=2)
            rating = fake.random_int(min=1, max=5)
            writer.writerow([productid, buyerid, dtime, review, rating])
        print(f'{num_reviews} product reviews generated')

def gen_seller_reviews(num_reviews, sellers):
    with open('SellerReview1.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Seller Reviews...', end=' ', flush=True)
        seen_combinations = set()
        
        for _ in range(num_reviews):
            while True:
                seller = fake.random_element(sellers)
                sellerid = seller[0]
                buyerid = fake.random_int(min=0, max=num_users-1)
                if buyerid != sellerid and (sellerid, buyerid) not in seen_combinations:
                    seen_combinations.add((sellerid, buyerid))
                    break
            
            dtime = fake.date_time_between(start_date='-1y', end_date='now')
            review = fake.paragraph(nb_sentences=2)
            rating = fake.random_int(min=1, max=5)
            writer.writerow([buyerid, sellerid, dtime, rating, review])
        print(f'{num_reviews} seller reviews generated')

def main():
    # Generate all data
    sellers = gen_users_and_sellers(num_users)
    available_pids = gen_products(num_products, sellers)
    gen_carts(num_cart_items, available_pids)
    purchase_combinations = gen_purchases(num_purchases, available_pids)
    gen_product_reviews(num_product_reviews, available_pids)
    gen_seller_reviews(num_seller_reviews, sellers)

if __name__ == "__main__":
    main()
