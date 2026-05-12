from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
try:
    from flask_mail import Mail, Message
    FLASK_MAIL_AVAILABLE = True
except ImportError:
    FLASK_MAIL_AVAILABLE = False
    print("Warning: Flask-Mail not installed. Email notifications will be disabled.")
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models.db import get_db_connection, init_database
from routes.contact_routes import contact_bp
from routes.currency_routes import currency_bp
import secrets
from config.config import Config
from datetime import datetime
import os
from uuid import uuid4
from models.db_reviews import (
    save_review,
    get_review_stats,
    get_reviews_by_product,
    get_reviews_for_admin,
    update_review_status,
    delete_review,
)
from models.db_coupons import (
    create_coupon,
    update_coupon,
    get_coupon_by_code,
    get_all_coupons,
    increment_coupon_usage,
)
from utils.currency_service import currency_service
from utils.csrf import generate_csrf_token
from models.db_currencies import get_base_currency, get_all_currencies, ensure_currency_base, get_currency_by_code

app = Flask(__name__)

# Load configuration
app.config.from_object('config.config.Config')
app.config.from_pyfile('instance/config.py', silent=True)

# Generate secret key if not exists
if not app.config.get('SECRET_KEY'):
    app.config['SECRET_KEY'] = secrets.token_hex(32)

DEFAULT_BASE_CURRENCY_CODE = 'EGP'

# Initialize database - FIXED: Removed deprecated before_first_request
def ensure_admin_user():
    """Ensure admin user exists using environment-configured credentials"""
    conn = get_db_connection()
    if not conn:
        print("[WARNING] Failed to connect to database - cannot create admin user")
        return False
    
    # Load admin credentials from environment or use secure defaults
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'changeme')
    
    cursor = conn.cursor()
    try:
        # Check if admin user exists
        cursor.execute('SELECT user_id, is_admin FROM Users.users WHERE email = ?', (ADMIN_EMAIL,))
        admin_row = cursor.fetchone()
        
        if not admin_row:
            # Create admin user
            admin_password_hash = generate_password_hash(ADMIN_PASSWORD)
            print(f"[OK] Creating admin user with email: {ADMIN_EMAIL}")
            cursor.execute('''
                INSERT INTO Users.users (username, email, password_hash, first_name, last_name, is_admin)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('admin', ADMIN_EMAIL, admin_password_hash, 'Admin', 'User', 1))
            conn.commit()
            print("[OK] Admin user created successfully")
            
            # Verify the user was created
            cursor.execute('SELECT user_id, username, email, is_admin FROM Users.users WHERE email = ?', (ADMIN_EMAIL,))
            verify_user = cursor.fetchone()
            if verify_user:
                print(f"[OK] Verified admin user: ID={verify_user[0]}, Email={verify_user[2]}")
            return True
        else:
            # Update existing admin to ensure is_admin = 1 and password is correct
            admin_user_id = admin_row[0]
            admin_is_admin = admin_row[1]
            
            # Update password to ensure it's correct
            admin_password_hash = generate_password_hash(ADMIN_PASSWORD)
            cursor.execute('''
                UPDATE Users.users 
                SET password_hash = ?, is_admin = 1
                WHERE email = ?
            ''', (admin_password_hash, ADMIN_EMAIL))
            conn.commit()
            
            if not admin_is_admin:
                print(f"[OK] Admin privileges granted to {ADMIN_EMAIL}")
            else:
                print(f"[OK] Admin user verified: {ADMIN_EMAIL}")
            return True
    except Exception as e:
        import traceback
        print(f"[WARNING] Error ensuring admin user: {e}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

with app.app_context():
    init_database()
    ensure_currency_base(DEFAULT_BASE_CURRENCY_CODE)
    ensure_admin_user()

app.register_blueprint(contact_bp)
app.register_blueprint(currency_bp)

# Initialize Flask-Mail if available
if FLASK_MAIL_AVAILABLE:
    mail = Mail(app)
else:
    mail = None

SHIPPING_FLAT_RATE = 10
TAX_RATE = 0.10

UPLOAD_DIR = os.path.join(app.root_path, 'static', 'uploads', 'products')
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config.setdefault('PRODUCT_UPLOAD_FOLDER', UPLOAD_DIR)
app.config.setdefault('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
app.config.setdefault('MAX_IMAGE_COUNT', 6)

def generate_order_number():
    '''Generate unique order number'''
    return f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

def get_cart_total(target_currency_code=None):
    '''Calculate cart total in base currency (or target currency if provided)'''
    cart = session.get('cart', {})
    if not cart:
        return 0.0

    base_currency = get_base_currency()
    base_code = base_currency['code'] if base_currency else None

    total_in_base = 0.0
    for item in cart.values():
        source_code = item.get('currency_code') or base_code
        price_in_base = currency_service.convert_price(
            item.get('price', 0),
            source_code,
            base_code
        )
        total_in_base += price_in_base * item.get('quantity', 1)

    if target_currency_code:
        return currency_service.convert_price(total_in_base, base_code, target_currency_code)

    return total_in_base

def get_cart_count():
    '''Get total items in cart'''
    cart = session.get('cart', {})
    return sum(item['quantity'] for item in cart.values())


def allowed_image(filename: str) -> bool:
    return (
        filename
        and '.' in filename
        and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_IMAGE_EXTENSIONS']
    )


def convert_amount(amount, from_currency_code, to_currency_code):
    """Convert amount between currencies with graceful fallback"""
    if amount is None:
        return 0.0

    return currency_service.convert_price(amount, from_currency_code, to_currency_code)


@app.context_processor
def utility_processor():
    def resolve_image_url(path: str):
        if not path:
            return url_for('static', filename='images/placeholder.png')
        if path.startswith('http://') or path.startswith('https://') or path.startswith('/static/'):
            return path
        return url_for('static', filename=path.lstrip('/'))

    def format_currency_price(price, currency_code=None, product_currency_code=None):
        """Format price with EGP currency symbol for templates"""
        egp_currency = get_currency_by_code('EGP')
        if not egp_currency:
            return f"EGP{float(price or 0):.2f}"

        converted_price = float(price or 0)
        
        symbol = egp_currency.get('symbol', 'EGP')
        return f"{symbol}{converted_price:.2f}"

    return {
        'resolve_image_url': resolve_image_url,
        'format_currency_price': format_currency_price,
        'csrf_token': generate_csrf_token()
    }


def fetch_product_images(cursor, product_id: int):
    cursor.execute(
        '''
        SELECT image_id, image_url, display_order
        FROM Products.product_images
        WHERE product_id = ?
        ORDER BY display_order ASC, image_id ASC
        ''',
        (product_id,),
    )
    return [
        {'image_id': row[0], 'image_url': row[1], 'display_order': row[2]}
        for row in cursor.fetchall()
    ]


def sync_primary_image(cursor, product_id: int):
    cursor.execute(
        '''
        SELECT TOP 1 image_url
        FROM Products.product_images
        WHERE product_id = ?
        ORDER BY display_order ASC, image_id ASC
        ''',
        (product_id,),
    )
    row = cursor.fetchone()
    cursor.execute(
        'UPDATE Products.products SET image_url = ? WHERE product_id = ?',
        (row[0] if row else None, product_id),
    )


password = "admin123"
hashed = generate_password_hash(password)
print(f"Password hash: {hashed}")

@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return render_template('index.html', 
                             featured_products=[],
                             latest_products=[],
                             upcoming_matches=[],
                             cart_count=get_cart_count())
    
    try:
        cursor = conn.cursor()
        
        # Get featured products with category and brand names
        cursor.execute('''
            SELECT TOP 6 
                p.product_id,
                p.name,
                ISNULL(c.name, 'Uncategorized') AS category,
                p.description,
                p.price,
                p.stock_quantity,
                p.image_url,
                ISNULL(b.name, 'No Brand') AS brand,
                p.size,
                p.color,
                p.is_featured,
                p.created_at,
                NULL AS currency_code
            FROM Products.products p
            LEFT JOIN Products.categories c ON p.category_id = c.category_id
            LEFT JOIN Products.brands b ON p.brand_id = b.brand_id
            WHERE p.is_featured = 1
            ORDER BY p.created_at DESC
        ''')
        # Convert to list of tuples to avoid closed connection issues
        featured_products = [tuple(row) for row in cursor.fetchall()]

        # Get latest products (most recently added)
        cursor.execute('''
            SELECT TOP 6 
                p.product_id,
                p.name,
                ISNULL(c.name, 'Uncategorized') AS category,
                p.description,
                p.price,
                p.stock_quantity,
                p.image_url,
                ISNULL(b.name, 'No Brand') AS brand,
                p.size,
                p.color,
                p.is_featured,
                p.created_at,
                NULL AS currency_code
            FROM Products.products p
            LEFT JOIN Products.categories c ON p.category_id = c.category_id
            LEFT JOIN Products.brands b ON p.brand_id = b.brand_id
            ORDER BY p.created_at DESC
        ''')
        # Convert to list of tuples to avoid closed connection issues
        latest_products = [tuple(row) for row in cursor.fetchall()]

        # Get upcoming matches
        cursor.execute('''
            SELECT TOP 4 
                t.ticket_id,
                m.match_name,
                m.home_team,
                m.away_team,
                m.stadium,
                m.match_date,
                t.seat_section,
                t.seat_number,
                t.price,
                t.is_available,
                t.image_url,
                NULL AS currency_code
            FROM Tickets.tickets t
            INNER JOIN Tickets.matches m ON t.match_id = m.match_id
            WHERE m.match_date > GETDATE() AND t.is_available = 1
            ORDER BY m.match_date ASC
        ''')
        # Convert to list of tuples to avoid closed connection issues
        upcoming_matches = [tuple(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        conn = None
        
        return render_template('index.html', 
                             featured_products=featured_products,
                             latest_products=latest_products,
                             upcoming_matches=upcoming_matches,
                             cart_count=get_cart_count())
    except Exception as e:
        if conn:
            conn.close()
        flash(f'Error loading page: {str(e)}', 'error')
        return render_template('index.html', 
                             featured_products=[],
                             latest_products=[],
                             upcoming_matches=[],
                             cart_count=get_cart_count())


@app.route('/products')
def products():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return render_template('products.html', 
                             products=[],
                             categories=[],
                             selected_category='',
                             search_term='',
                             cart_count=get_cart_count())
    
    try:
        cursor = conn.cursor()
        
        # Get filters
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        
        # Build query with explicit columns and joins
        query = '''
            SELECT 
                p.product_id,
                p.name,
                ISNULL(c.name, 'Uncategorized') AS category,
                p.description,
                p.price,
                p.stock_quantity,
                p.image_url,
                ISNULL(b.name, 'No Brand') AS brand,
                p.size,
                p.color,
                p.is_featured,
                p.created_at,
                NULL AS currency_code
            FROM Products.products p
            LEFT JOIN Products.categories c ON p.category_id = c.category_id
            LEFT JOIN Products.brands b ON p.brand_id = b.brand_id
            WHERE 1=1
        '''
        params = []
        
        if category:
            query += ' AND c.name = ?'
            params.append(category)
        
        if search:
            query += ' AND (p.name LIKE ? OR p.description LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        query += ' ORDER BY p.created_at DESC'
        
        cursor.execute(query, params)
        # Convert to list of tuples to avoid closed connection issues
        products_list = [tuple(row) for row in cursor.fetchall()]
        
        # Get categories (return names for template)
        cursor.execute('SELECT name FROM Products.categories ORDER BY name')
        categories = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        conn = None
        
        return render_template('products.html', 
                             products=products_list,
                             categories=categories,
                             selected_category=category,
                             search_term=search,
                             cart_count=get_cart_count())
    except Exception as e:
        if conn:
            conn.close()
        flash(f'Error loading products: {str(e)}', 'error')
        return render_template('products.html', 
                             products=[],
                             categories=[],
                             selected_category='',
                             search_term='',
                             cart_count=get_cart_count())

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('products'))
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                p.product_id,
                p.name,
                ISNULL(c.name, 'Uncategorized') AS category,
                p.description,
                p.price,
                p.stock_quantity,
                p.image_url,
                ISNULL(b.name, 'No Brand') AS brand,
                p.size,
                p.color,
                p.is_featured,
                p.created_at,
                NULL AS currency_code
            FROM Products.products p
            LEFT JOIN Products.categories c ON p.category_id = c.category_id
            LEFT JOIN Products.brands b ON p.brand_id = b.brand_id
            WHERE p.product_id = ?
        ''', (product_id,))
        product_row = cursor.fetchone()
        # Convert to tuple to avoid closed connection issues
        product = tuple(product_row) if product_row else None
        
        cursor.execute(
            '''
            SELECT image_url
            FROM Products.product_images
            WHERE product_id = ?
            ORDER BY display_order ASC, image_id ASC
            ''',
            (product_id,),
        )
        gallery_images = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        conn = None
        
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('products'))

        if not gallery_images and product[6]:
            gallery_images = [product[6]]

        if not gallery_images:
            gallery_images = ['https://via.placeholder.com/600x600?text=Image']

        review_stats = get_review_stats(product_id)
        reviews = get_reviews_by_product(product_id)
        
        return render_template('product_detail.html', 
                             product=product,
                             product_gallery=gallery_images,
                             review_stats=review_stats,
                             reviews=reviews,
                             cart_count=get_cart_count())
    except Exception as e:
        if conn:
            conn.close()
        flash(f'Error loading product: {str(e)}', 'error')
        return redirect(url_for('products'))


@app.route('/tickets')
def tickets():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return render_template('tickets.html', 
                             tickets=[],
                             cart_count=get_cart_count())
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                t.ticket_id,
                m.match_name,
                m.home_team,
                m.away_team,
                m.stadium,
                m.match_date,
                t.seat_section,
                t.seat_number,
                t.price,
                t.is_available,
                t.image_url,
                NULL AS currency_code
            FROM Tickets.tickets t
            INNER JOIN Tickets.matches m ON t.match_id = m.match_id
            WHERE m.match_date > GETDATE() AND t.is_available = 1
            ORDER BY m.match_date ASC
        ''')
        # Convert to list of tuples to avoid closed connection issues
        tickets_list = [tuple(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        conn = None
        
        return render_template('tickets.html', 
                             tickets=tickets_list,
                             cart_count=get_cart_count())
    except Exception as e:
        if conn:
            conn.close()
        flash(f'Error loading tickets: {str(e)}', 'error')
        return render_template('tickets.html', 
                             tickets=[],
                             cart_count=get_cart_count())


@app.route('/cart')
def cart():
    cart_items = session.get('cart', {})

    user_currency = currency_service.get_user_currency(session)
    target_code = user_currency['code']
    base_currency = get_base_currency()
    base_code = base_currency['code'] if base_currency else target_code

    subtotal_base, subtotal_converted, subtotal_formatted = currency_service.calculate_cart_total(
        cart_items.values(),
        target_code
    )

    # Calculate discount if coupon exists
    coupon = session.get('coupon')
    discount_base = 0.0
    discount_converted = 0.0
    discount_formatted = ''
    
    if coupon:
        discount_type = coupon.get('discount_type', 'percentage')
        discount_value = float(coupon.get('discount_value', 0))
        
        if discount_type == 'percentage':
            discount_base = subtotal_base * (discount_value / 100)
        else:  # fixed
            discount_base = min(discount_value, subtotal_base)
        
        discount_converted = convert_amount(discount_base, base_code, target_code)
        discount_formatted = currency_service.format_price(discount_converted, target_code)

    shipping_base = float(SHIPPING_FLAT_RATE)
    shipping_converted = convert_amount(shipping_base, base_code, target_code)
    shipping_formatted = currency_service.format_price(shipping_converted, target_code)

    # Calculate tax on subtotal after discount
    grand_subtotal_base = max(subtotal_base - discount_base, 0)
    grand_subtotal_converted = max(subtotal_converted - discount_converted, 0)
    
    tax_base = grand_subtotal_base * TAX_RATE
    tax_converted = convert_amount(tax_base, base_code, target_code)
    tax_formatted = currency_service.format_price(tax_converted, target_code)

    total_base = grand_subtotal_base + shipping_base + tax_base
    total_converted = grand_subtotal_converted + shipping_converted + tax_converted
    total_formatted = currency_service.format_price(total_converted, target_code)

    return render_template('cart.html',
                         cart=cart_items,
                         coupon=coupon,
                         subtotal=subtotal_converted,
                         subtotal_formatted=subtotal_formatted,
                         subtotal_base=subtotal_base,
                         discount_base=discount_base,
                         discount_converted=discount_converted,
                         discount_formatted=discount_formatted,
                         shipping_base=shipping_base,
                         shipping_converted=shipping_converted,
                         shipping_formatted=shipping_formatted,
                         tax_base=tax_base,
                         tax_converted=tax_converted,
                         tax_formatted=tax_formatted,
                         total_base=total_base,
                         total_converted=total_converted,
                         total_formatted=total_formatted,
                         tax_rate=TAX_RATE,
                         cart_count=get_cart_count())

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request'})
    
    item_id = data.get('item_id')
    item_type = data.get('item_type')  # 'product' or 'ticket'
    quantity = int(data.get('quantity', 1))
    
    if not item_id or not item_type:
        return jsonify({'success': False, 'message': 'Invalid item'})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'})
    
    try:
        cursor = conn.cursor()
        
        # Get item details
        if item_type == 'product':
            cursor.execute('''
                SELECT 
                    p.product_id,
                    p.name,
                    ISNULL(c.name, 'Uncategorized') AS category,
                    p.description,
                    p.price,
                    p.stock_quantity,
                    p.image_url,
                    ISNULL(b.name, 'No Brand') AS brand,
                    p.size,
                    p.color,
                    p.is_featured,
                    p.created_at,
                    NULL AS currency_code
                FROM Products.products p
                LEFT JOIN Products.categories c ON p.category_id = c.category_id
                LEFT JOIN Products.brands b ON p.brand_id = b.brand_id
                WHERE p.product_id = ?
            ''', (item_id,))
        else:
            cursor.execute('''
                SELECT 
                    t.ticket_id,
                    m.match_name,
                    m.home_team,
                    m.away_team,
                    m.stadium,
                    m.match_date,
                    t.seat_section,
                    t.seat_number,
                    t.price,
                    t.is_available,
                    t.image_url,
                    NULL AS currency_code
                FROM Tickets.tickets t
                INNER JOIN Tickets.matches m ON t.match_id = m.match_id
                WHERE t.ticket_id = ?
            ''', (item_id,))
        
        item = cursor.fetchone()
        # Convert to tuple to avoid closed connection issues
        if item:
            item = tuple(item)
        cursor.close()
        conn.close()
        
        if not item:
            return jsonify({'success': False, 'message': 'Item not found'})
        
        # Initialize cart
        if 'cart' not in session:
            session['cart'] = {}
        
        cart_key = f"{item_type}_{item_id}"
        
        if cart_key in session['cart']:
            session['cart'][cart_key]['quantity'] += quantity
        else:
            # Get price (always in base currency EGP)
            # For products: price is at index 4, for tickets: price is at index 8
            item_price = float(item[4] if item_type == 'product' else item[8])
            egp_currency = get_currency_by_code('EGP')
            
            session['cart'][cart_key] = {
                'id': item_id,
                'type': item_type,
                'name': item[1],  # name field
                'price': item_price,  # price in EGP
                'currency_code': 'EGP',  # Always EGP
                'currency_symbol': egp_currency.get('symbol', 'EGP') if egp_currency else 'EGP',
                'quantity': quantity,
                'image': item[6] if item_type == 'product' else (item[10] if len(item) > 10 else None)
            }
        
        session.modified = True
        
        return jsonify({
            'success': True, 
            'message': 'Item added to cart',
            'cart_count': get_cart_count()
        })
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/remove-from-cart/<cart_key>')
def remove_from_cart(cart_key):
    if 'cart' in session and cart_key in session['cart']:
        del session['cart'][cart_key]
        session.modified = True
        flash('Item removed from cart', 'success')
    return redirect(url_for('cart'))

@app.route('/update-cart', methods=['POST'])
def update_cart():
    data = request.get_json()
    if not data:
        return jsonify({'success': False})
    
    cart_key = data.get('cart_key')
    quantity = int(data.get('quantity', 1))
    
    if 'cart' in session and cart_key in session['cart']:
        if quantity > 0:
            session['cart'][cart_key]['quantity'] = quantity
        else:
            del session['cart'][cart_key]
        session.modified = True
        return jsonify({
            'success': True,
            'total': get_cart_total(),
            'cart_count': get_cart_count()
        })
    
    return jsonify({'success': False})

@app.route('/apply-coupon', methods=['POST'])
def apply_coupon():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request'})
    
    coupon_code = data.get('code', '').strip().upper()
    if not coupon_code:
        return jsonify({'success': False, 'message': 'Please enter a coupon code'})
    
    # Get coupon from database
    coupon = get_coupon_by_code(coupon_code)
    if not coupon:
        return jsonify({'success': False, 'message': 'Invalid coupon code'})
    
    # Check if coupon is active
    if not coupon.get('is_active'):
        return jsonify({'success': False, 'message': 'This coupon is not active'})
    
    # Check if coupon has expired
    if coupon.get('expires_at'):
        from datetime import datetime
        if datetime.now() > coupon['expires_at']:
            return jsonify({'success': False, 'message': 'This coupon has expired'})
    
    # Check usage limit
    if coupon.get('usage_limit'):
        if coupon.get('times_used', 0) >= coupon['usage_limit']:
            return jsonify({'success': False, 'message': 'This coupon has reached its usage limit'})
    
    # Check minimum order amount
    # Get cart total in base currency (EGP)
    base_currency = get_base_currency()
    base_code = base_currency['code'] if base_currency else 'EGP'
    
    # Calculate cart total in base currency (EGP)
    cart_items = session.get('cart', {})
    if cart_items:
        _, cart_total_in_base, _ = currency_service.calculate_cart_total(
            cart_items.values(),
            base_code
        )
    else:
        cart_total_in_base = 0.0
    
    if coupon.get('min_order_amount'):
        # min_order_amount is stored in base currency (EGP)
        # Treat it as EGP since EGP is now the base currency
        min_order_amount_base = float(coupon['min_order_amount'])
        
        # Compare both values in base currency (EGP)
        if cart_total_in_base < min_order_amount_base:
            # Format error message in EGP
            min_order_formatted = currency_service.format_price(min_order_amount_base, 'EGP')
            cart_total_formatted = currency_service.format_price(cart_total_in_base, 'EGP')
            return jsonify({
                'success': False, 
                'message': f'Minimum order amount of {min_order_formatted} required. Your cart total is {cart_total_formatted}.'
            })
    
    # Calculate discount amount using cart total in base currency
    discount_type = coupon.get('discount_type', 'percentage')
    discount_value = float(coupon.get('discount_value', 0))
    
    if discount_type == 'percentage':
        discount_amount = cart_total_in_base * (discount_value / 100)
    else:  # fixed - discount_value is also in base currency
        discount_amount = min(discount_value, cart_total_in_base)
    
    # Store coupon in session with calculated discount
    coupon_data = {
        'coupon_id': coupon['coupon_id'],
        'code': coupon['code'],
        'discount_type': discount_type,
        'discount_value': discount_value,
        'discount_amount': discount_amount
    }
    session['coupon'] = coupon_data
    session.modified = True
    
    return jsonify({
        'success': True,
        'message': 'Coupon applied successfully!',
        'discount_amount': discount_amount,
        'discount_type': discount_type,
        'discount_value': discount_value
    })

@app.route('/remove-coupon', methods=['POST'])
def remove_coupon():
    if 'coupon' in session:
        session.pop('coupon', None)
        session.modified = True
        return jsonify({'success': True, 'message': 'Coupon removed'})
    return jsonify({'success': False, 'message': 'No coupon to remove'})


@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        flash('Please login to checkout', 'warning')
        return redirect(url_for('login'))
    
    cart_items = session.get('cart', {})
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('products'))
    
    coupon = session.get('coupon')
    user_currency = currency_service.get_user_currency(session)
    target_code = user_currency['code']
    base_currency = get_base_currency()
    base_code = base_currency['code'] if base_currency else target_code

    subtotal_base, subtotal_converted, subtotal_formatted = currency_service.calculate_cart_total(
        cart_items.values(),
        target_code
    )

    discount_base = 0
    if coupon:
        discount_type = coupon.get('discount_type', 'percentage')
        discount_value = float(coupon.get('discount_value', 0))

        if discount_type == 'percentage':
            discount_base = subtotal_base * (discount_value / 100)
        else:
            discount_base = min(discount_value, subtotal_base)

    discount_converted = convert_amount(discount_base, base_code, target_code)
    discount_formatted = currency_service.format_price(discount_converted, target_code)

    grand_base = max(subtotal_base - discount_base, 0)
    grand_converted = max(subtotal_converted - discount_converted, 0)
    grand_formatted = currency_service.format_price(grand_converted, target_code)

    shipping_base = float(SHIPPING_FLAT_RATE)
    shipping_converted = convert_amount(shipping_base, base_code, target_code)
    shipping_formatted = currency_service.format_price(shipping_converted, target_code)

    tax_base = grand_base * TAX_RATE
    tax_converted = convert_amount(tax_base, base_code, target_code)
    tax_formatted = currency_service.format_price(tax_converted, target_code)

    total_base = grand_base + shipping_base + tax_base
    total_converted = grand_converted + shipping_converted + tax_converted
    total_formatted = currency_service.format_price(total_converted, target_code)

    return render_template('checkout.html', 
                         cart=cart_items,
                         coupon=coupon,
                         subtotal_formatted=subtotal_formatted,
                         subtotal_base=subtotal_base,
                         discount_formatted=discount_formatted,
                         discount_base=discount_base,
                         grand_formatted=grand_formatted,
                         grand_base=grand_base,
                         shipping_formatted=shipping_formatted,
                         shipping_base=shipping_base,
                         tax_formatted=tax_formatted,
                         tax_base=tax_base,
                         total_formatted=total_formatted,
                         total_base=total_base,
                         tax_rate=TAX_RATE,
                         cart_count=get_cart_count())

@app.route('/place-order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    cart_items = session.get('cart', {})
    if not cart_items:
        return jsonify({'success': False, 'message': 'Cart is empty'})
    
    # Get shipping details
    address = request.form.get('address')
    city = request.form.get('city')
    country = request.form.get('country')
    
    if not all([address, city, country]):
        return jsonify({'success': False, 'message': 'Please provide all shipping details'})
    
    shipping_address = f"{address}, {city}, {country}"
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'})
    
    cursor = conn.cursor()
    
    try:
        # Get user's selected currency (default to EGP)
        user_currency = currency_service.get_user_currency(session)
        user_currency_code = user_currency.get('code', 'EGP') if user_currency else 'EGP'

        # Calculate order total in base currency (EGP)
        base_currency = get_base_currency()
        base_code = base_currency.get('code', 'EGP') if base_currency else 'EGP'
        _, cart_total_in_base, _ = currency_service.calculate_cart_total(cart_items.values(), base_code)

        # Calculate discount if coupon exists (all in base currency EGP)
        coupon = session.get('coupon')
        discount_amount = 0
        if coupon:
            discount_type = coupon.get('discount_type', 'percentage')
            discount_value = float(coupon.get('discount_value', 0))

            if discount_type == 'percentage':
                discount_amount = cart_total_in_base * (discount_value / 100)
            else:  # fixed
                discount_amount = min(discount_value, cart_total_in_base)

        total_amount_in_base = max(cart_total_in_base - discount_amount, 0)

        # Create order
        order_number = generate_order_number()

        # Create shipping address first
        cursor.execute('''
            INSERT INTO Core.addresses (street_address, city, country)
            OUTPUT INSERTED.address_id
            VALUES (?, ?, ?)
        ''', (address, city, country))
        address_result = cursor.fetchone()
        shipping_address_id = address_result[0] if address_result else None
        
        # Insert order
        cursor.execute('''
            INSERT INTO Orders.orders (user_id, order_number, total_amount, status, shipping_address_id)
            OUTPUT INSERTED.order_id
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], order_number, total_amount_in_base, 'Pending', shipping_address_id))
        
        # Get order ID from the OUTPUT clause
        result = cursor.fetchone()
        if not result:
            raise Exception("Failed to retrieve order ID after insert")
        order_id = result[0]
        
        # Check stock availability BEFORE inserting order items
        # This prevents race conditions and ensures we have enough stock
        insufficient_stock_items = []
        
        for item in cart_items.values():
            if item['type'] == 'product':
                # Check current stock for this product
                cursor.execute('''
                    SELECT stock_quantity, name
                    FROM Products.products
                    WHERE product_id = ?
                ''', (item['id'],))
                
                stock_result = cursor.fetchone()
                if not stock_result:
                    raise Exception(f"Product with ID {item['id']} not found")
                
                current_stock = int(stock_result[0])
                product_name = stock_result[1]
                requested_quantity = int(item['quantity'])
                
                # Check if we have enough stock
                if current_stock < requested_quantity:
                    insufficient_stock_items.append({
                        'name': product_name,
                        'requested': requested_quantity,
                        'available': current_stock
                    })
        
        # If any items have insufficient stock, reject the order
        if insufficient_stock_items:
            conn.rollback()
            cursor.close()
            conn.close()
            conn = None
            
            error_messages = []
            for stock_item in insufficient_stock_items:
                if stock_item['available'] == 0:
                    error_messages.append(f"{stock_item['name']} is out of stock.")
                else:
                    error_messages.append(
                        f"{stock_item['name']}: Only {stock_item['available']} available, but {stock_item['requested']} requested."
                    )
            
            return jsonify({
                'success': False,
                'message': ' '.join(error_messages)
            })
        
        # All stock checks passed - proceed with order
        # Insert order items (prices are already in base currency EGP)
        for item in cart_items.values():
            # Price is already in base currency (EGP) from cart
            item_price_in_base = float(item.get('price', 0))

            if item['type'] == 'product':
                # Insert order item
                cursor.execute('''
                    INSERT INTO Orders.order_items (order_id, product_id, item_type, quantity, price)
                    VALUES (?, ?, ?, ?, ?)
                ''', (order_id, item['id'], 'product', item['quantity'], item_price_in_base))

                # Reduce stock atomically using a single UPDATE with WHERE clause
                # This ensures we don't go below 0 and prevents race conditions
                cursor.execute('''
                    UPDATE Products.products
                    SET stock_quantity = stock_quantity - ?
                    WHERE product_id = ? AND stock_quantity >= ?
                ''', (item['quantity'], item['id'], item['quantity']))
                
                # Verify the stock was actually updated
                if cursor.rowcount == 0:
                    # Stock was insufficient (another order might have taken it)
                    conn.rollback()
                    cursor.close()
                    conn.close()
                    conn = None
                    return jsonify({
                        'success': False,
                        'message': 'Order failed: Stock was updated by another order. Please try again.'
                    })
            else:
                # Handle tickets
                cursor.execute('''
                    INSERT INTO Orders.order_items (order_id, ticket_id, item_type, quantity, price)
                    VALUES (?, ?, ?, ?, ?)
                ''', (order_id, item['id'], 'ticket', item['quantity'], item_price_in_base))

                # Mark ticket as sold (only if available)
                cursor.execute('''
                    UPDATE Tickets.tickets
                    SET is_available = 0
                    WHERE ticket_id = ? AND is_available = 1
                ''', (item['id'],))
                
                # Verify the ticket was actually updated
                if cursor.rowcount == 0:
                    # Ticket was already sold
                    conn.rollback()
                    cursor.close()
                    conn.close()
                    conn = None
                    return jsonify({
                        'success': False,
                        'message': 'Order failed: One or more tickets are no longer available. Please try again.'
                    })
        
        conn.commit()

        if coupon:
            increment_coupon_usage(coupon['coupon_id'])
            session.pop('coupon', None)
        
        # Get user email for confirmation email
        cursor.execute('SELECT email, first_name, last_name, username FROM Users.users WHERE user_id = ?', (session['user_id'],))
        user_info = cursor.fetchone()
        user_email = user_info[0] if user_info else None
        user_name = f"{user_info[1]} {user_info[2]}" if user_info and user_info[1] and user_info[2] else (user_info[3] if user_info else 'Customer')
        
        cursor.close()
        conn.close()
        conn = None
        
        # Send order confirmation email (non-blocking - don't fail order if email fails)
        if user_email:
            try:
                send_order_confirmation_email(user_email, user_name, order_number, total_amount_in_base, base_code)
            except Exception as email_error:
                # Log error but don't fail the order
                print(f"Error sending order confirmation email: {email_error}")
        
        # Clear cart
        session['cart'] = {}
        session.modified = True
        
        return jsonify({
            'success': True, 
            'message': 'Order placed successfully!',
            'order_number': order_number
        })
        
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except:
                pass
            try:
                cursor.close()
            except:
                pass
            try:
                conn.close()
            except:
                pass
            conn = None
        error_msg = str(e)
        print(f"Error placing order: {error_msg}")
        return jsonify({'success': False, 'message': f'Error placing order: {error_msg}'})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Basic validation
        if not email or not password:
            flash('Please provide email and password', 'error')
            return render_template('login.html', cart_count=get_cart_count())

        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please check your database configuration.', 'error')
            print("ERROR: Failed to connect to database during login attempt")
            return render_template('login.html', cart_count=get_cart_count())

        try:
            cursor = conn.cursor()
            # Fetch only required columns to avoid index mistakes
            print(f"Attempting login for email: {email}")
            cursor.execute('SELECT user_id, username, password_hash, is_admin FROM Users.users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if not user:
                print(f"User not found for email: {email}")
                flash('Invalid email or password', 'error')
                cursor.close()
                conn.close()
                return render_template('login.html', cart_count=get_cart_count())
            
            print(f"User found: {user[1]}, is_admin: {user[3]}")
            password_valid = check_password_hash(user[2], password)
            print(f"Password valid: {password_valid}")
            
            cursor.close()
            conn.close()

            if password_valid:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['is_admin'] = bool(user[3])  # Correct admin flag
                flash('Login successful!', 'success')
                print(f"Login successful, is_admin: {bool(user[3])}")
                # Redirect admin to admin page, regular users to index
                if bool(user[3]):  # is_admin
                    return redirect(url_for('admin'))
                return redirect(url_for('index'))
            else:
                print("Password mismatch")
                flash('Invalid email or password', 'error')

        except Exception as e:
            if conn:
                conn.close()
            flash(f'Login error: {str(e)}', 'error')

    return render_template('login.html', cart_count=get_cart_count())


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        
        if not all([username, email, password]):
            flash('Please provide all required fields', 'error')
            return render_template('register.html', cart_count=get_cart_count())
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('register.html', cart_count=get_cart_count())
        
        if not any(c.isupper() for c in password):
            flash('Password must contain at least one uppercase letter', 'error')
            return render_template('register.html', cart_count=get_cart_count())
        
        if not any(c.isdigit() for c in password):
            flash('Password must contain at least one number', 'error')
            return render_template('register.html', cart_count=get_cart_count())
        
        password_hash = generate_password_hash(password)
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return redirect(url_for('register'))
        
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO Users.users (username, email, password_hash, first_name, last_name, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, first_name, last_name, phone))
            
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            conn.rollback()
            flash('Username or email already exists', 'error')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return render_template('register.html', cart_count=get_cart_count())

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


@app.route('/admin')
def admin():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    if not session.get('is_admin'):
        flash('Access denied - Admin privileges required', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection error', 'error')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute('SELECT COUNT(*) FROM Products.products')
        total_products = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Tickets.tickets WHERE is_available = 1')
        total_tickets = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Orders.orders')
        total_orders = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(total_amount) FROM Orders.orders')
        total_revenue = cursor.fetchone()[0] or 0
        total_revenue = float(total_revenue)
        
        # Get product options
        cursor.execute('SELECT product_id, name FROM Products.products ORDER BY name')
        
        # CRITICAL: Call fetchall() ONCE, store result, validate, then iterate
        # NEVER call fetchall() directly inside a comprehension
        product_rows_raw = None
        try:
            # Call the method with parentheses - store result immediately
            product_rows_raw = cursor.fetchall()
            
            # Validate: Check if it's callable (should NEVER be)
            if callable(product_rows_raw):
                raise ValueError("CRITICAL: fetchall() returned a callable object - this should never happen!")
            
            # Convert to list safely
            if product_rows_raw is None:
                product_rows = []
            elif isinstance(product_rows_raw, list):
                product_rows = product_rows_raw
            elif isinstance(product_rows_raw, tuple):
                product_rows = list(product_rows_raw)
            else:
                # Try to convert if iterable
                try:
                    product_rows = list(product_rows_raw)
                except (TypeError, ValueError) as conv_err:
                    raise ValueError(f"Cannot convert fetchall() result to list: {conv_err}. Type: {type(product_rows_raw)}")
        except Exception as e:
            print(f"CRITICAL ERROR fetching product options: {e}")
            print(f"product_rows_raw type: {type(product_rows_raw)}, value: {product_rows_raw}")
            product_rows = []
        
        # Final safety check: MUST be a list, NOT callable
        if callable(product_rows):
            raise ValueError("CRITICAL: product_rows is still callable after processing!")
        if not isinstance(product_rows, list):
            print(f"WARNING: product_rows is not a list, converting. Type: {type(product_rows)}")
            product_rows = []
        
        # NOW safely build the list comprehension using the validated list
        product_options = [
            {'id': row[0], 'name': row[1]}
            for row in product_rows
        ]
        
        # Get recent orders with customer information
        cursor.execute('''
            SELECT TOP 10 
                o.order_number,
                COALESCE(u.first_name + ' ' + u.last_name, u.username, 'Unknown') AS customer,
                o.total_amount,
                o.status,
                o.created_at
            FROM Orders.orders o
            LEFT JOIN Users.users u ON o.user_id = u.user_id
            ORDER BY o.created_at DESC
        ''')
        order_rows = cursor.fetchall()
        
        # Convert to list of dictionaries for template
        recent_orders = []
        for row in order_rows:
            recent_orders.append({
                'order_number': row[0],
                'customer': row[1] if row[1] else 'Unknown',
                'total_amount': float(row[2]) if row[2] else 0.0,
                'status': row[3] if row[3] else 'Pending',
                'created_at': row[4] if row[4] else datetime.now()
            })
        
        cursor.close()
        conn.close()
        
        return render_template('admin.html',
                             total_products=total_products,
                             total_tickets=total_tickets,
                             total_orders=total_orders,
                             total_revenue=total_revenue,
                             product_options=product_options,
                             recent_orders=recent_orders,
                             cart_count=get_cart_count())
    except Exception as e:
        if conn:
            conn.close()
        flash(f'Error loading admin panel: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/admin/add-product', methods=['POST'])
def add_product():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'})
        
        cursor = conn.cursor()
        
        # Get or create category
        category_name = request.form.get('category', '').strip()
        category_id = None
        if category_name:
            cursor.execute('SELECT category_id FROM Products.categories WHERE name = ?', (category_name,))
            cat_row = cursor.fetchone()
            if cat_row:
                category_id = cat_row[0]
            else:
                cursor.execute('INSERT INTO Products.categories (name) OUTPUT INSERTED.category_id VALUES (?)', (category_name,))
                category_id = cursor.fetchone()[0]
        
        # Get or create brand
        brand_name = request.form.get('brand', '').strip()
        brand_id = None
        if brand_name:
            cursor.execute('SELECT brand_id FROM Products.brands WHERE name = ?', (brand_name,))
            brand_row = cursor.fetchone()
            if brand_row:
                brand_id = brand_row[0]
            else:
                cursor.execute('INSERT INTO Products.brands (name) OUTPUT INSERTED.brand_id VALUES (?)', (brand_name,))
                brand_id = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO Products.products (name, category_id, description, price, stock_quantity, image_url, brand_id, size, color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form.get('name'),
            category_id,
            request.form.get('description'),
            request.form.get('price'),
            request.form.get('stock_quantity'),
            request.form.get('image_url'),
            brand_id,
            request.form.get('size'),
            request.form.get('color')
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product added successfully'})
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/admin/reviews')
def admin_reviews():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    if not session.get('is_admin'):
        flash('Access denied - Admin privileges required', 'error')
        return redirect(url_for('index'))

    status_filter = request.args.get('status') or None
    reviews = get_reviews_for_admin(status_filter)
    return render_template(
        'admin/reviews.html',
        reviews=reviews,
        status_filter=status_filter or 'All',
        cart_count=get_cart_count(),
    )


@app.route('/admin/reviews/<int:review_id>/status', methods=['POST'])
def admin_update_review_status(review_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    status = request.form.get('status')
    if status not in {'Approved', 'Rejected', 'Pending'}:
        return jsonify({'success': False, 'message': 'Invalid status supplied.'}), 400

    try:
        success = update_review_status(review_id, status)
        return jsonify({'success': success})
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


@app.route('/admin/reviews/<int:review_id>', methods=['DELETE'])
def admin_delete_review(review_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    try:
        success = delete_review(review_id)
        return jsonify({'success': success})
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500

@app.route('/admin/products/<int:product_id>/images', methods=['GET'])
def get_product_images_api(product_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'}), 500

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT name, image_url FROM Products.products WHERE product_id = ?', (product_id,))
        product_row = cursor.fetchone()
        if not product_row:
            return jsonify({'success': False, 'message': 'Product not found'}), 404

        product_name, primary_image = product_row
        images = fetch_product_images(cursor, product_id)

        if not images and primary_image:
            cursor.execute(
                '''
                INSERT INTO Products.product_images (product_id, image_url, display_order)
                VALUES (?, ?, 0)
                ''',
                (product_id, primary_image),
            )
            conn.commit()
            images = fetch_product_images(cursor, product_id)

        return jsonify({
            'success': True,
            'product': {'id': product_id, 'name': product_name},
            'images': images,
            'max_images': app.config['MAX_IMAGE_COUNT'],
        })
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/admin/products/<int:product_id>/images', methods=['POST'])
def upload_product_images(product_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    files = request.files.getlist('images')
    if not files:
        return jsonify({'success': False, 'message': 'Please choose at least one image.'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'}), 500

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT COUNT(*) FROM Products.product_images WHERE product_id = ?', (product_id,))
        existing_count = cursor.fetchone()[0]
        max_images = app.config['MAX_IMAGE_COUNT']

        if existing_count >= max_images:
            return jsonify({'success': False, 'message': f'Maximum of {max_images} images reached.'}), 400

        saved_any = False
        for upload in files:
            if not upload or not upload.filename:
                continue
            if existing_count >= max_images:
                break
            if not allowed_image(upload.filename):
                return jsonify({'success': False, 'message': 'Invalid file type. Please upload images only.'}), 400

            filename = secure_filename(upload.filename)
            unique_name = f"{uuid4().hex}_{filename}"
            upload_path = os.path.join(app.config['PRODUCT_UPLOAD_FOLDER'], unique_name)
            upload.save(upload_path)

            image_url = f"/static/uploads/products/{unique_name}"
            cursor.execute(
                '''
                INSERT INTO Products.product_images (product_id, image_url, display_order)
                VALUES (?, ?, ?)
                ''',
                (product_id, image_url, existing_count),
            )
            existing_count += 1
            saved_any = True

        if not saved_any:
            conn.rollback()
            return jsonify({'success': False, 'message': 'No images were uploaded.'}), 400

        sync_primary_image(cursor, product_id)
        conn.commit()

        images = fetch_product_images(cursor, product_id)
        return jsonify({'success': True, 'images': images, 'max_images': max_images})
    except Exception as exc:
        conn.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/admin/products/<int:product_id>/images/<int:image_id>', methods=['DELETE'])
def delete_product_image(product_id, image_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'}), 500

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT image_url FROM Products.product_images
            WHERE image_id = ? AND product_id = ?
            ''',
            (image_id, product_id),
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Image not found.'}), 404

        image_url = row[0]
        cursor.execute('DELETE FROM Products.product_images WHERE image_id = ? AND product_id = ?', (image_id, product_id))

        cursor.execute(
            '''
            WITH Ordered AS (
                SELECT image_id,
                       ROW_NUMBER() OVER (ORDER BY display_order ASC, image_id ASC) - 1 AS rn
                FROM Products.product_images
                WHERE product_id = ?
            )
            UPDATE Products.product_images
            SET display_order = Ordered.rn
            FROM Products.product_images
            INNER JOIN Ordered ON Products.product_images.image_id = Ordered.image_id
            ''',
            (product_id,),
        )

        sync_primary_image(cursor, product_id)
        conn.commit()

        if image_url.startswith('/static/'):
            file_path = os.path.join(app.root_path, image_url.lstrip('/'))
            if os.path.exists(file_path):
                os.remove(file_path)

        images = fetch_product_images(cursor, product_id)
        return jsonify({'success': True, 'images': images})
    except Exception as exc:
        conn.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/admin/products/<int:product_id>/images/reorder', methods=['POST'])
def reorder_product_images(product_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    order_payload = request.get_json(silent=True) or {}
    image_order = order_payload.get('order', [])
    if not isinstance(image_order, list):
        return jsonify({'success': False, 'message': 'Invalid order payload.'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database error'}), 500

    cursor = conn.cursor()
    try:
        for index, image_id in enumerate(image_order):
            cursor.execute(
                '''
                UPDATE Products.product_images
                SET display_order = ?
                WHERE image_id = ? AND product_id = ?
                ''',
                (index, image_id, product_id),
            )

        sync_primary_image(cursor, product_id)
        conn.commit()

        images = fetch_product_images(cursor, product_id)
        return jsonify({'success': True, 'images': images})
    except Exception as exc:
        conn.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/admin/add-ticket', methods=['POST'])
def add_ticket():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'})
        
        cursor = conn.cursor()
        
        # Get form data
        match_name = request.form.get('match_name', '').strip()
        home_team = request.form.get('home_team', '').strip()
        away_team = request.form.get('away_team', '').strip()
        stadium = request.form.get('stadium', '').strip()
        match_date_str = request.form.get('match_date', '').strip()
        seat_section = request.form.get('seat_section', '').strip()
        seat_number = request.form.get('seat_number', '').strip()
        price_str = request.form.get('price', '').strip()
        image_url = request.form.get('image_url', '').strip()
        
        # Validate required fields
        if not all([match_name, home_team, away_team, stadium, match_date_str, price_str]):
            return jsonify({'success': False, 'message': 'Please fill in all required fields'})
        
        # Parse and convert date to SQL Server compatible format
        # Try multiple date formats
        match_date = None
        date_formats = [
            '%Y-%m-%d %H:%M:%S',  # 2024-01-15 14:30:00
            '%Y-%m-%d %H:%M',     # 2024-01-15 14:30
            '%Y-%m-%dT%H:%M:%S',  # 2024-01-15T14:30:00 (ISO format)
            '%Y-%m-%dT%H:%M',     # 2024-01-15T14:30
            '%Y-%m-%d',           # 2024-01-15
            '%m/%d/%Y %H:%M:%S',  # 01/15/2024 14:30:00
            '%m/%d/%Y %H:%M',     # 01/15/2024 14:30
            '%m/%d/%Y',           # 01/15/2024
            '%d/%m/%Y %H:%M:%S',  # 15/01/2024 14:30:00
            '%d/%m/%Y %H:%M',     # 15/01/2024 14:30
            '%d/%m/%Y',           # 15/01/2024
        ]
        
        for date_format in date_formats:
            try:
                match_date = datetime.strptime(match_date_str, date_format)
                break
            except ValueError:
                continue
        
        if match_date is None:
            return jsonify({
                'success': False, 
                'message': f'Invalid date format. Please use YYYY-MM-DD or YYYY-MM-DD HH:MM format. Received: {match_date_str}'
            })
        
        # Convert price to float
        try:
            price = float(price_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid price format'})
        
        # First, create or get match
        cursor.execute('''
            SELECT match_id FROM Tickets.matches 
            WHERE match_name = ? AND home_team = ? AND away_team = ? AND stadium = ? AND match_date = ?
        ''', (match_name, home_team, away_team, stadium, match_date))
        match_row = cursor.fetchone()
        if match_row:
            match_id = match_row[0]
        else:
            cursor.execute('''
                INSERT INTO Tickets.matches (match_name, home_team, away_team, stadium, match_date)
                OUTPUT INSERTED.match_id
                VALUES (?, ?, ?, ?, ?)
            ''', (match_name, home_team, away_team, stadium, match_date))
            match_id = cursor.fetchone()[0]
        
        # Insert ticket with match_id
        cursor.execute('''
            INSERT INTO Tickets.tickets (match_id, seat_section, seat_number, price, image_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            match_id,
            seat_section,
            seat_number,
            price,
            image_url if image_url else None
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        conn = None
        
        return jsonify({'success': True, 'message': 'Ticket added successfully'})
    except Exception as e:
        if conn:
            try:
                conn.rollback()
                conn.close()
            except:
                pass
            conn = None
        error_msg = str(e)
        print(f"Error adding ticket: {error_msg}")
        return jsonify({'success': False, 'message': f'Error adding ticket: {error_msg}'})


@app.route('/admin/coupons')
def admin_coupons():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    if not session.get('is_admin'):
        flash('Access denied - Admin privileges required', 'error')
        return redirect(url_for('index'))

    coupons = get_all_coupons()
    return render_template(
        'admin/coupons.html',
        coupons=coupons,
        cart_count=get_cart_count(),
    )

@app.route('/admin/coupons', methods=['POST'])
def admin_create_coupon():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    try:
        code = request.form.get('code', '').strip().upper()
        discount_type = request.form.get('discount_type', 'percentage')
        
        try:
            discount_value = float(request.form.get('discount_value', 0))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid discount value'}), 400
        
        min_order_amount = request.form.get('min_order_amount', '').strip()
        min_order_amount = float(min_order_amount) if min_order_amount else None
        
        usage_limit = request.form.get('usage_limit', '').strip()
        usage_limit = int(usage_limit) if usage_limit else None
        
        expires_at = request.form.get('expires_at', '').strip()
        if expires_at:
            try:
                expires_at = datetime.strptime(expires_at, '%Y-%m-%dT%H:%M')
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DDTHH:MM'}), 400
        else:
            expires_at = None

        if not code:
            return jsonify({'success': False, 'message': 'Coupon code is required'}), 400

        if discount_value <= 0:
            return jsonify({'success': False, 'message': 'Discount value must be greater than 0'}), 400

        # Create the coupon - errors will be caught and returned
        result = create_coupon(code, discount_type, discount_value, min_order_amount, usage_limit, expires_at)
        
        if result:
            # Double-check by querying the database
            from models.db_coupons import get_coupon_by_code
            verify_coupon = get_coupon_by_code(code)
            if verify_coupon:
                return jsonify({
                    'success': True, 
                    'message': f'Coupon "{code}" created successfully and saved to {Config.DB_DATABASE}',
                    'coupon_id': verify_coupon.get('coupon_id')
                })
            else:
                return jsonify({
                    'success': False, 
                    'message': 'Coupon creation reported success but could not be verified in database. Check server logs.'
                }), 500
        else:
            return jsonify({'success': False, 'message': 'Failed to create coupon. Check server logs for details.'})
    except ValueError as e:
        return jsonify({'success': False, 'message': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        error_msg = str(e)
        print(f"Error in admin_create_coupon: {error_msg}")
        if 'UNIQUE constraint' in error_msg or 'duplicate' in error_msg.lower():
            return jsonify({'success': False, 'message': 'Coupon code already exists'}), 400
        return jsonify({'success': False, 'message': f'Database error: {error_msg}'}), 500

@app.route('/admin/test-db')
def test_database():
    """Test route to verify database connection and table"""
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Access denied'}), 403
    
    from models.db import get_db_connection
    from config.config import Config
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'status': 'error',
                'message': 'Failed to connect to database',
                'config': {
                    'server': Config.DB_SERVER,
                    'database': Config.DB_DATABASE,
                    'username': Config.DB_USERNAME
                }
            })
        
        cursor = conn.cursor()
        
        # Get current database
        cursor.execute("SELECT DB_NAME()")
        current_db = cursor.fetchone()[0]
        
        # Check if coupons table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'Marketing' AND TABLE_NAME = 'coupons'
        """)
        table_exists = cursor.fetchone()[0] > 0
        
        # Get table structure if exists
        table_info = None
        if table_exists:
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'Marketing' AND TABLE_NAME = 'coupons'
                ORDER BY ORDINAL_POSITION
            """)
            table_info = [{'name': row[0], 'type': row[1], 'nullable': row[2]} for row in cursor.fetchall()]
        
        # Count existing coupons
        coupon_count = 0
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM Marketing.coupons")
            coupon_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'current_database': current_db,
            'expected_database': Config.DB_DATABASE,
            'database_match': current_db == Config.DB_DATABASE,
            'table_exists': table_exists,
            'table_structure': table_info,
            'coupon_count': coupon_count,
            'config': {
                'server': Config.DB_SERVER,
                'database': Config.DB_DATABASE,
                'username': Config.DB_USERNAME
            }
        })
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/admin/coupons/<int:coupon_id>', methods=['POST'])
def admin_update_coupon(coupon_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    try:
        data = {
            'code': request.form.get('code', '').strip().upper(),
            'discount_type': request.form.get('discount_type', 'percentage'),
            'discount_value': float(request.form.get('discount_value', 0)),
            'min_order_amount': request.form.get('min_order_amount'),
            'usage_limit': request.form.get('usage_limit'),
            'expires_at': request.form.get('expires_at'),
            'is_active': request.form.get('is_active') == 'on'
        }

        if data['min_order_amount']:
            data['min_order_amount'] = float(data['min_order_amount'])
        else:
            data['min_order_amount'] = None

        if data['usage_limit']:
            data['usage_limit'] = int(data['usage_limit'])
        else:
            data['usage_limit'] = None

        if data['expires_at']:
            data['expires_at'] = datetime.strptime(data['expires_at'], '%Y-%m-%dT%H:%M')
        else:
            data['expires_at'] = None

        if update_coupon(coupon_id, data):
            return jsonify({'success': True, 'message': 'Coupon updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update coupon'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/product/<int:product_id>/reviews', methods=['POST'])
def submit_product_review(product_id):
    if 'user_id' not in session:
        flash('Please login to write a review.', 'error')
        return redirect(url_for('login'))

    rating = int(request.form.get('rating', 0) or 0)
    title = request.form.get('title', '').strip() or None
    content = request.form.get('content', '').strip()

    if rating < 1 or rating > 5:
        flash('Please provide a rating between 1 and 5 stars.', 'error')
        return redirect(url_for('product_detail', product_id=product_id))

    if not content:
        flash('Review content cannot be empty.', 'error')
        return redirect(url_for('product_detail', product_id=product_id))

    try:
        save_review(product_id, session['user_id'], rating, title, content)
        flash('Review submitted! It will appear once approved by an admin.', 'success')
    except Exception as exc:
        flash(f'Unable to submit review: {exc}', 'error')

    return redirect(url_for('product_detail', product_id=product_id))


def send_order_confirmation_email(user_email, user_name, order_number, total_amount, currency_code):
    """Send order confirmation email after order is placed"""
    if not FLASK_MAIL_AVAILABLE or not mail:
        print(f"Order confirmation email skipped (Flask-Mail not available): Order {order_number}")
        return False
    
    try:
        # Get currency symbol
        currency = get_currency_by_code(currency_code)
        currency_symbol = currency['symbol'] if currency else currency_code
        
        # Create email message
        msg = Message(
            subject='Order Confirmed',
            recipients=[user_email],
            sender=app.config.get('MAIL_DEFAULT_SENDER') or app.config.get('MAIL_USERNAME')
        )
        
        # Email body (HTML)
        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Order Confirmed</h2>
                <p>Dear {user_name},</p>
                <p>Your order has been confirmed. Thank you for shopping with us!</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Order Details</h3>
                    <p><strong>Order Number:</strong> {order_number}</p>
                    <p><strong>Total Amount:</strong> {currency_symbol}{total_amount:.2f}</p>
                </div>
                
                <p>We will process your order and send you updates soon.</p>
                <p>Thank you for shopping with us!</p>
                <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">
                    Football Store<br>
                    This is an automated message. Please do not reply.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        msg.body = f"""
Order Confirmed

Dear {user_name},

Your order has been confirmed. Thank you for shopping with us!

Order Details:
- Order Number: {order_number}
- Total Amount: {currency_symbol}{total_amount:.2f}

We will process your order and send you updates soon.

Thank you for shopping with us!

Football Store
This is an automated message. Please do not reply.
        """
        
        mail.send(msg)
        print(f"Order confirmation email sent successfully to {user_email} for order {order_number}")
        return True
    except Exception as e:
        print(f"Error sending order confirmation email: {str(e)}")
        return False


def send_order_status_email(user_email, user_name, order_number, order_status, order_items, total_amount, shipping_address):
    """Send email notification when order status changes"""
    if not FLASK_MAIL_AVAILABLE or not mail:
        print(f"Email notification skipped (Flask-Mail not available): Order {order_number} status changed to {order_status}")
        return False
    
    try:
        # Status descriptions
        status_descriptions = {
            'Pending': 'Your order has been received and is being processed.',
            'Processing': 'Your order is being prepared for shipment.',
            'Shipped': 'Your order has been shipped and is on its way to you.',
            'Out for Delivery': 'Your order is out for delivery and will arrive soon.',
            'Delivered': 'Your order has been delivered successfully.',
            'Cancelled': 'Your order has been cancelled.'
        }
        
        status_description = status_descriptions.get(order_status, 'Your order status has been updated.')
        
        # Create email message
        msg = Message(
            subject=f'Order {order_number} Status Update - {order_status}',
            recipients=[user_email],
            sender=app.config.get('MAIL_DEFAULT_SENDER') or app.config.get('MAIL_USERNAME')
        )
        
        # Email body (HTML)
        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Order Status Update</h2>
                <p>Dear {user_name},</p>
                <p>{status_description}</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Order Details</h3>
                    <p><strong>Order Number:</strong> {order_number}</p>
                    <p><strong>Status:</strong> <span style="color: #28a745; font-weight: bold;">{order_status}</span></p>
                    <p><strong>Total Amount:</strong> EGP{total_amount:.2f}</p>
                    <p><strong>Shipping Address:</strong> {shipping_address or 'N/A'}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3>Order Items:</h3>
                    <ul>
                        {''.join([f'<li>{item["name"]} x{item["quantity"]} - EGP{item["price"]:.2f}</li>' for item in order_items])}
                    </ul>
                </div>
                
                <p>Thank you for shopping with us!</p>
                <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">
                    Football Store<br>
                    This is an automated message. Please do not reply.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        msg.body = f"""
Order Status Update

Dear {user_name},

{status_description}

Order Details:
- Order Number: {order_number}
- Status: {order_status}
- Total Amount: EGP{total_amount:.2f}
- Shipping Address: {shipping_address or 'N/A'}

Order Items:
{chr(10).join([f'- {item["name"]} x{item["quantity"]} - EGP{item["price"]:.2f}' for item in order_items])}

Thank you for shopping with us!

Football Store
This is an automated message. Please do not reply.
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False




@app.context_processor
def inject_currencies():
    """Return EGP currency only"""
    egp_currency = get_currency_by_code('EGP')
    if not egp_currency:
        egp_currency = {'code': 'EGP', 'symbol': 'EGP', 'is_base': True}
    return {
        'currencies': [egp_currency],
        'current_currency': egp_currency,
        'base_currency': egp_currency
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

