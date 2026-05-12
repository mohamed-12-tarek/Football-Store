from models.db import get_db_connection

def ensure_currency_base(code):
    """Set the provided currency code as the base currency."""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        # Check if currencies table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'currencies'
        """)
        table_exists = cursor.fetchone()[0] > 0
        
        if not table_exists:
            print(f"[WARNING] Currencies table does not exist - skipping currency setup (using {code} as default)")
            return True  # Return True to not break app initialization
        
        cursor.execute("SELECT currency_id FROM currencies WHERE UPPER(code) = UPPER(?)", (code,))
        row = cursor.fetchone()
        if not row:
            return False

        cursor.execute("UPDATE currencies SET is_base = CASE WHEN UPPER(code) = UPPER(?) THEN 1 ELSE 0 END", (code,))
        cursor.execute("""
            UPDATE currencies
            SET exchange_rate = 1, is_active = 1
            WHERE UPPER(code) = UPPER(?)
        """, (code,))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error ensuring base currency {code}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_all_currencies(active_only=True):
    """Get all currencies from database"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        if active_only:
            cursor.execute("SELECT * FROM currencies WHERE is_active = 1 ORDER BY name")
        else:
            cursor.execute("SELECT * FROM currencies ORDER BY name")

        currencies = []
        for row in cursor.fetchall():
            currencies.append({
                'currency_id': row[0],
                'name': row[1],
                'code': row[2],
                'symbol': row[3],
                'exchange_rate': float(row[4]),
                'is_active': bool(row[5]),
                'is_base': bool(row[6]),
                'created_at': row[7],
                'updated_at': row[8]
            })

        return currencies
    except Exception as e:
        print(f"Error getting currencies: {e}")
        return []
    finally:
        conn.close()

def get_currency_by_id(currency_id):
    """Get currency by ID"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM currencies WHERE currency_id = ?", (currency_id,))
        row = cursor.fetchone()

        if row:
            return {
                'currency_id': row[0],
                'name': row[1],
                'code': row[2],
                'symbol': row[3],
                'exchange_rate': float(row[4]),
                'is_active': bool(row[5]),
                'is_base': bool(row[6]),
                'created_at': row[7],
                'updated_at': row[8]
            }
        return None
    except Exception as e:
        print(f"Error getting currency by ID: {e}")
        return None
    finally:
        conn.close()

def get_currency_by_code(code):
    """Get currency by code (e.g., 'USD', 'EUR') - returns EGP default if table doesn't exist"""
    conn = get_db_connection()
    if not conn:
        # Return default EGP if code is EGP
        if code == 'EGP':
            return {'code': 'EGP', 'symbol': 'EGP', 'is_base': True}
        return None

    try:
        cursor = conn.cursor()
        # Check if currencies table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'currencies'
        """)
        table_exists = cursor.fetchone()[0] > 0
        
        if not table_exists:
            # Return default EGP if code is EGP
            if code == 'EGP':
                return {'code': 'EGP', 'symbol': 'EGP', 'is_base': True}
            return None
        
        cursor.execute("SELECT * FROM currencies WHERE code = ? AND is_active = 1", (code,))
        row = cursor.fetchone()

        if row:
            return {
                'currency_id': row[0],
                'name': row[1],
                'code': row[2],
                'symbol': row[3],
                'exchange_rate': float(row[4]),
                'is_active': bool(row[5]),
                'is_base': bool(row[6]),
                'created_at': row[7],
                'updated_at': row[8]
            }
        return None
    except Exception as e:
        print(f"Error getting currency by code: {e}")
        # Return default EGP if code is EGP
        if code == 'EGP':
            return {'code': 'EGP', 'symbol': 'EGP', 'is_base': True}
        return None
    finally:
        if conn:
            conn.close()

def get_base_currency():
    """Get the base currency - returns EGP default if currencies table doesn't exist"""
    conn = get_db_connection()
    if not conn:
        # Return default EGP if no connection
        return {'code': 'EGP', 'symbol': 'EGP', 'is_base': True}

    try:
        cursor = conn.cursor()
        # Check if currencies table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'currencies'
        """)
        table_exists = cursor.fetchone()[0] > 0
        
        if not table_exists:
            # Return default EGP currency
            return {'code': 'EGP', 'symbol': 'EGP', 'is_base': True}
        
        cursor.execute("SELECT * FROM currencies WHERE is_base = 1 AND is_active = 1")
        row = cursor.fetchone()

        if row:
            return {
                'currency_id': row[0],
                'name': row[1],
                'code': row[2],
                'symbol': row[3],
                'exchange_rate': float(row[4]),
                'is_active': bool(row[5]),
                'is_base': bool(row[6]),
                'created_at': row[7],
                'updated_at': row[8]
            }
        # If no base currency found, return EGP default
        return {'code': 'EGP', 'symbol': 'EGP', 'is_base': True}
    except Exception as e:
        print(f"Error getting base currency: {e}")
        # Return default EGP on error
        return {'code': 'EGP', 'symbol': 'EGP', 'is_base': True}
    finally:
        if conn:
            conn.close()

def create_currency(name, code, symbol, exchange_rate, is_active=True, is_base=False):
    """Create a new currency"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # If setting as base currency, unset any existing base currency
        if is_base:
            cursor.execute("UPDATE currencies SET is_base = 0 WHERE is_base = 1")

        cursor.execute('''
            INSERT INTO currencies (name, code, symbol, exchange_rate, is_active, is_base)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, code, symbol, exchange_rate, is_active, is_base))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating currency: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_currency(currency_id, name, code, symbol, exchange_rate, is_active, is_base=False):
    """Update an existing currency"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # If setting as base currency, unset any existing base currency
        if is_base:
            cursor.execute("UPDATE currencies SET is_base = 0 WHERE is_base = 1")

        cursor.execute('''
            UPDATE currencies
            SET name = ?, code = ?, symbol = ?, exchange_rate = ?, is_active = ?, is_base = ?, updated_at = GETDATE()
            WHERE currency_id = ?
        ''', (name, code, symbol, exchange_rate, is_active, is_base, currency_id))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating currency: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_currency(currency_id):
    """Delete a currency (only if not referenced by products/orders)"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Check if currency is referenced by any products or orders
        cursor.execute("SELECT COUNT(*) FROM products WHERE currency_id = ?", (currency_id,))
        product_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE currency_id = ?", (currency_id,))
        order_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tickets WHERE currency_id = ?", (currency_id,))
        ticket_count = cursor.fetchone()[0]

        if product_count > 0 or order_count > 0 or ticket_count > 0:
            print(f"Cannot delete currency: referenced by {product_count} products, {order_count} orders, {ticket_count} tickets")
            return False

        # Check if it's the base currency
        cursor.execute("SELECT is_base FROM currencies WHERE currency_id = ?", (currency_id,))
        row = cursor.fetchone()
        if row and row[0]:
            print("Cannot delete base currency")
            return False

        cursor.execute("DELETE FROM currencies WHERE currency_id = ?", (currency_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting currency: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_exchange_rate(from_currency_code, to_currency_code):
    """Get exchange rate between two currencies"""
    from_currency = get_currency_by_code(from_currency_code)
    to_currency = get_currency_by_code(to_currency_code)

    if not from_currency or not to_currency:
        return None

    # Convert from base currency units to target currency
    # Rate = (from_rate / to_rate) where rates are relative to base
    return from_currency['exchange_rate'] / to_currency['exchange_rate']

