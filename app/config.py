import os
from urllib.parse import quote_plus

class Config(object):
    # Get the base directory of your project (316MiniAmazon)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'\
        .format(os.environ.get('DB_USER'),
                quote_plus(os.environ.get('DB_PASSWORD')),
                os.environ.get('DB_HOST'),
                os.environ.get('DB_PORT'),
                os.environ.get('DB_NAME'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Set UPLOAD_FOLDER to be in the db directory
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'db', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}