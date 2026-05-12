import pyodbc
from werkzeug.security import generate_password_hash
from config.config import Config


def get_db_connection():
    '''Create and return a database connection'''
    try:
        # Build connection string with explicit database
        conn_str = (
            f'DRIVER={Config.DB_DRIVER};'
            f'SERVER={Config.DB_SERVER};'
            f'DATABASE={Config.DB_DATABASE};'
        )
       
        # Add authentication - use SQL Server Authentication if username/password provided
        if hasattr(Config, 'DB_USERNAME') and Config.DB_USERNAME and hasattr(Config, 'DB_PASSWORD') and Config.DB_PASSWORD:
            conn_str += f'UID={Config.DB_USERNAME};PWD={Config.DB_PASSWORD};'
        else:
            # Use Windows Authentication if no credentials provided
            conn_str += 'Trusted_Connection=yes;'
       
        # Add additional connection options for better compatibility
        conn_str += 'TrustServerCertificate=yes;'
       
        print(f"Connecting to SQL Server: {Config.DB_SERVER}")
        print(f"Database: {Config.DB_DATABASE}")
        print(f"Connection string: {conn_str.replace(Config.DB_PASSWORD, '***') if hasattr(Config, 'DB_PASSWORD') else conn_str}")
       
        # Connect with explicit autocommit=False to ensure transactions work
        conn = pyodbc.connect(conn_str, autocommit=False)
       
        # Verify we're connected to the correct database
        cursor = conn.cursor()
        cursor.execute("SELECT DB_NAME()")
        actual_db = cursor.fetchone()[0]
        cursor.close()
       
        if actual_db != Config.DB_DATABASE:
            print(f"[WARNING] Connected to '{actual_db}' but expected '{Config.DB_DATABASE}'")
            print(f"[WARNING] This might cause data to be saved to the wrong database!")
        else:
            print(f"[OK] Successfully connected to {Config.DB_DATABASE}")
       
        return conn
    except Exception as e:
        print(f"[ERROR] Database connection error: {e}")
        print(f"  Server: {Config.DB_SERVER}")
        print(f"  Database: {Config.DB_DATABASE}")
        return None


def ensure_database_exists():
    '''Ensure the database exists, create it if it doesn't'''
    try:
        master_conn_str = (
            f'DRIVER={Config.DB_DRIVER};'
            f'SERVER={Config.DB_SERVER};'
            f'DATABASE=master;'
        )
        if hasattr(Config, 'DB_USERNAME') and Config.DB_USERNAME and hasattr(Config, 'DB_PASSWORD') and Config.DB_PASSWORD:
            master_conn_str += f'UID={Config.DB_USERNAME};PWD={Config.DB_PASSWORD};'
        else:
            master_conn_str += 'Trusted_Connection=yes;'
        master_conn_str += 'TrustServerCertificate=yes;'
       
        master_conn = pyodbc.connect(master_conn_str)
        master_cursor = master_conn.cursor()
       
        master_cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{Config.DB_DATABASE}'")
        if not master_cursor.fetchone():
            print(f"[INFO] Database '{Config.DB_DATABASE}' does not exist. Creating it...")
            master_cursor.execute(f"CREATE DATABASE [{Config.DB_DATABASE}]")
            master_conn.commit()
            print(f"[OK] Database '{Config.DB_DATABASE}' created successfully")
        else:
            print(f"[OK] Database '{Config.DB_DATABASE}' already exists")
       
        master_cursor.close()
        master_conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Ensuring database exists: {e}")
        return False


def init_database():
    '''Initialize database - Check if new schema-based structure exists, skip old table creation if it does.'''
    # First ensure the database exists
    if not ensure_database_exists():
        print("Failed to ensure database exists")
        return False
   
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return False


    cursor = conn.cursor()
   
    try:
        # Check if new schema-based structure exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'Products' AND TABLE_NAME = 'products'
        """)
        new_structure_exists = cursor.fetchone()[0] > 0
       
        if new_structure_exists:
            print("[OK] New schema-based database structure detected (FootballStoreDB with schemas)")
            print("[OK] Skipping old table creation - using existing schema structure")
            cursor.close()
            cursor = None
            conn.close()
            conn = None
            return True
       
       
    except Exception as e:
        print(f"Error checking database structure: {e}")
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass
   
   
    print("[INFO] Skipping automatic table creation - please use the provided SQL script")
    return True


    # Create Users table
    create_users = '''
    CREATE TABLE users (
        user_id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(50) NOT NULL UNIQUE,
        email NVARCHAR(100) NOT NULL UNIQUE,
        password_hash NVARCHAR(255) NOT NULL,
        first_name NVARCHAR(50) NOT NULL,
        last_name NVARCHAR(50) NOT NULL,
        phone NVARCHAR(20),
        address NVARCHAR(255),
        city NVARCHAR(100),
        country NVARCHAR(100),
        is_admin BIT DEFAULT 0,
        created_at DATETIME2 DEFAULT GETDATE()
    );
    '''
   
    # Create Products table
    create_products = '''
    CREATE TABLE products (
        product_id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(200) NOT NULL,
        category NVARCHAR(50) NOT NULL,
        description NVARCHAR(MAX),
        price DECIMAL(10,2) NOT NULL,
        currency_id INT NULL,
        stock_quantity INT NOT NULL DEFAULT 0,
        image_url NVARCHAR(500),
        brand NVARCHAR(100),
        size NVARCHAR(50),
        color NVARCHAR(50),
        is_featured BIT DEFAULT 0,
        created_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (currency_id) REFERENCES currencies(currency_id)
    );
    '''
   
    # Create Tickets table
    create_tickets = '''
    CREATE TABLE tickets (
        ticket_id INT IDENTITY(1,1) PRIMARY KEY,
        match_name NVARCHAR(200) NOT NULL,
        home_team NVARCHAR(100) NOT NULL,
        away_team NVARCHAR(100) NOT NULL,
        stadium NVARCHAR(200) NOT NULL,
        match_date DATETIME2 NOT NULL,
        seat_section NVARCHAR(50) NOT NULL,
        seat_number NVARCHAR(20) NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        currency_id INT NULL,
        is_available BIT DEFAULT 1,
        image_url NVARCHAR(500),
        created_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (currency_id) REFERENCES currencies(currency_id)
    );
    '''
   
    # Create Orders table
    create_orders = '''
    CREATE TABLE orders (
        order_id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        order_number NVARCHAR(50) NOT NULL UNIQUE,
        total_amount DECIMAL(10,2) NOT NULL,
        currency_id INT NULL,
        status NVARCHAR(20) DEFAULT 'Pending',
        shipping_address NVARCHAR(500),
        created_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (currency_id) REFERENCES currencies(currency_id)
    );
    '''
   
    # Create Order Items table
    create_order_items = '''
    CREATE TABLE order_items (
        order_item_id INT IDENTITY(1,1) PRIMARY KEY,
        order_id INT NOT NULL,
        product_id INT NULL,
        ticket_id INT NULL,
        item_type NVARCHAR(20) NOT NULL,
        quantity INT NOT NULL DEFAULT 1,
        price DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id),
        FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
    );
    '''


    create_product_images = '''
    CREATE TABLE product_images (
        image_id INT IDENTITY(1,1) PRIMARY KEY,
        product_id INT NOT NULL,
        image_url NVARCHAR(500) NOT NULL,
        display_order INT NOT NULL DEFAULT 0,
        created_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
    );
    '''


    create_product_reviews = '''
    CREATE TABLE product_reviews (
        review_id INT IDENTITY(1,1) PRIMARY KEY,
        product_id INT NOT NULL,
        user_id INT NOT NULL,
        rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
        title NVARCHAR(150) NULL,
        content NVARCHAR(MAX) NOT NULL,
        status NVARCHAR(20) NOT NULL DEFAULT 'Pending',
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    '''


    create_coupons = '''
    CREATE TABLE coupons (
        coupon_id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(50) NOT NULL UNIQUE,
        discount_type NVARCHAR(20) NOT NULL,
        discount_value DECIMAL(10,2) NOT NULL,
        min_order_amount DECIMAL(10,2) NULL,
        usage_limit INT NULL,
        times_used INT NOT NULL DEFAULT 0,
        expires_at DATETIME2 NULL,
        is_active BIT NOT NULL DEFAULT 1,
        created_at DATETIME2 DEFAULT GETDATE()
    );
    '''


    create_user_messages = '''
    CREATE TABLE user_messages (
        message_id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        email NVARCHAR(150) NOT NULL,
        subject NVARCHAR(200) NOT NULL,
        message NVARCHAR(MAX) NOT NULL,
        response NVARCHAR(MAX) NULL,
        status NVARCHAR(20) NOT NULL DEFAULT 'New',
        created_at DATETIME2 DEFAULT GETDATE(),
        replied_at DATETIME2 NULL
    );
    '''


    create_currencies = '''
    CREATE TABLE currencies (
        currency_id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        code NVARCHAR(10) NOT NULL UNIQUE,
        symbol NVARCHAR(10) NOT NULL,
        exchange_rate DECIMAL(10,6) NOT NULL,
        is_active BIT NOT NULL DEFAULT 1,
        is_base BIT NOT NULL DEFAULT 0,
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE()
    );
    '''
   
    tables_to_create = [
        ('users', create_users),
        ('products', create_products),
        ('tickets', create_tickets),
        ('orders', create_orders),
        ('order_items', create_order_items),
        ('product_images', create_product_images),
        ('product_reviews', create_product_reviews),
        ('coupons', create_coupons),
        ('user_messages', create_user_messages),
        ('currencies', create_currencies),
    ]


    try:
        for table_name, create_sql in tables_to_create:
            cursor.execute(_wrap_create(table_name, create_sql))


        # Add currency_id columns to existing tables if they don't exist
        alter_statements = [
            # Add currency_id to products table
            """
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('products') AND name = 'currency_id')
            BEGIN
                ALTER TABLE products ADD currency_id INT NULL;
                ALTER TABLE products ADD CONSTRAINT FK_products_currency FOREIGN KEY (currency_id) REFERENCES currencies(currency_id);
            END
            """,
            # Add currency_id to orders table
            """
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('orders') AND name = 'currency_id')
            BEGIN
                ALTER TABLE orders ADD currency_id INT NULL;
                ALTER TABLE orders ADD CONSTRAINT FK_orders_currency FOREIGN KEY (currency_id) REFERENCES currencies(currency_id);
            END
            """,
            # Add currency_id to tickets table
            """
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tickets') AND name = 'currency_id')
            BEGIN
                ALTER TABLE tickets ADD currency_id INT NULL;
                ALTER TABLE tickets ADD CONSTRAINT FK_tickets_currency FOREIGN KEY (currency_id) REFERENCES currencies(currency_id);
            END
            """
        ]


        for alter_sql in alter_statements:
            cursor.execute(alter_sql)


        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        if user_count == 0:
            insert_sample_data(cursor)


        conn.commit()
        print("Database checked successfully!")
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# def insert_sample_data(cursor):
#     '''Insert sample data for testing'''
   
#     # Insert admin user (password: admin123)
#     admin_password = generate_password_hash('admin123')
#     cursor.execute('''
#         INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin)
#         VALUES (?, ?, ?, ?, ?, ?)
#     ''', ('admin', 'admin@football.com', admin_password, 'Admin', 'User', 1))
   
#     # Insert sample products
#     products = [
#         ('Classic Football Jersey - Home', 'Jersey', 'Official team jersey with premium fabric', 89.99, 50,
#          'https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=500', 'Nike', 'M', 'Blue', 1),
#         ('Professional Football Boots', 'Shoes', 'High-performance boots with excellent grip', 149.99, 30,
#          'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=500', 'Adidas', '42', 'Black', 1),
#         ('Match Quality Football', 'Ball', 'FIFA approved match ball', 49.99, 100,
#          'https://images.unsplash.com/photo-1575361204480-aadea25e6e68?w=500', 'Nike', 'Size 5', 'White', 1),
#         ('Training Shorts', 'Apparel', 'Breathable training shorts', 34.99, 75,
#          'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=500', 'Puma', 'L', 'Black', 0),
#         ('Goalkeeper Gloves', 'Accessories', 'Professional goalkeeper gloves', 59.99, 40,
#          'https://images.unsplash.com/photo-1511886929837-354d827aae26?w=500', 'Adidas', 'Size 9', 'Green', 0),
#         ('Team Scarf', 'Accessories', 'Official team scarf', 24.99, 200,
#          'https://images.unsplash.com/photo-1595777216528-071e0127ccbf?w=500', 'Official', 'One Size', 'Blue', 0),
#     ]
   
#     # Get USD currency ID (base currency)
#     cursor.execute("SELECT currency_id FROM currencies WHERE code = 'USD'")
#     result = cursor.fetchone()
#     if result:
#         usd_currency_id = result[0]


#         for product in products:
#             cursor.execute('''
#                 INSERT INTO products (name, category, description, price, currency_id, stock_quantity, image_url, brand, size, color, is_featured)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#             ''', product + (usd_currency_id,))
#     else:
#         # Fallback if USD currency doesn't exist
#         for product in products:
#             cursor.execute('''
#                 INSERT INTO products (name, category, description, price, stock_quantity, image_url, brand, size, color, is_featured)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#             ''', product)


#     cursor.execute('SELECT product_id, image_url FROM products')
#     for product_id, image_url in cursor.fetchall():
#         for order_index in range(2):
#             cursor.execute('''
#                 INSERT INTO product_images (product_id, image_url, display_order)
#                 VALUES (?, ?, ?)
#             ''', (product_id, image_url, order_index))
   
#     # Insert sample tickets
#     tickets = [
#         ('Premier League Final', 'Manchester United', 'Liverpool FC', 'Old Trafford', '2024-05-15 19:45:00',
#          'North Stand', 'A12', 120.00, 1, 'https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=500'),
#         ('Champions League Semi-Final', 'Real Madrid', 'Bayern Munich', 'Santiago Bernabéu', '2024-04-20 20:00:00',
#          'East Stand', 'B45', 250.00, 1, 'https://images.unsplash.com/photo-1459865264687-595d652de67e?w=500'),
#         ('League Cup Match', 'Chelsea', 'Arsenal', 'Stamford Bridge', '2024-03-10 15:00:00',
#          'South Stand', 'C23', 85.00, 1, 'https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=500'),
#         ('Derby Match', 'Barcelona', 'Atletico Madrid', 'Camp Nou', '2024-06-01 21:00:00',
#          'West Stand', 'D67', 180.00, 1, 'https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=500'),
#     ]
   
#     if result:  # USD currency exists
#         for ticket in tickets:
#             cursor.execute('''
#                 INSERT INTO tickets (match_name, home_team, away_team, stadium, match_date, seat_section, seat_number, price, currency_id, is_available, image_url)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#             ''', ticket + (usd_currency_id,))
#     else:
#         # Fallback if USD currency doesn't exist
#         for ticket in tickets:
#             cursor.execute('''
#                 INSERT INTO tickets (match_name, home_team, away_team, stadium, match_date, seat_section, seat_number, price, is_available, image_url)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#             ''', ticket)


#     # Insert default currencies
#     currencies = [
#         ('US Dollar', 'USD', '$', 1.0, 1, 1),  # Base currency
#         ('Euro', 'EUR', '€', 0.85, 1, 0),
#         ('Egyptian Pound', 'EGP', '£', 0.032, 1, 0),
#         ('British Pound', 'GBP', '£', 0.73, 1, 0),
#     ]


#     for currency in currencies:
#         cursor.execute('''
#             INSERT INTO currencies (name, code, symbol, exchange_rate, is_active, is_base)
#             VALUES (?, ?, ?, ?, ?, ?)
#         ''', currency)


#     cursor.execute('''
#         INSERT INTO user_messages (name, email, subject, message)
#         VALUES (?, ?, ?, ?)
#     ''', (
#         'John Doe',
#         'john@example.com',
#         'Shipping Question',
#         'Hi, I would like to know the estimated shipping time for jerseys to Europe.'
#     ))

