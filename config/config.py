import os

class Config:
    # Database Configuration for SQL Server
    DB_DRIVER = os.environ.get('DB_DRIVER', '{ODBC Driver 17 for SQL Server}')
    DB_SERVER = os.environ.get('DB_SERVER', 'localhost')  
    DB_DATABASE = os.environ.get('DB_DATABASE', 'FootballStoreDB')
    DB_USERNAME = os.environ.get('DB_USERNAME', '')  
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')  
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set for production")
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'true')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')