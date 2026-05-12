from typing import Optional, Dict, Any, List
from datetime import datetime

from models.db import get_db_connection


def _parse_datetime(value):
    """Parse datetime from various formats"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Try common SQL Server datetime formats
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%dT%H:%M',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except (ValueError, TypeError):
                continue
    return value


def _row_to_coupon(row) -> Dict[str, Any]:
    keys = [
        'coupon_id',
        'code',
        'discount_type',
        'discount_value',
        'min_order_amount',
        'usage_limit',
        'times_used',
        'expires_at',
        'is_active',
        'created_at',
    ]
    coupon = {key: value for key, value in zip(keys, row)}
    
    # Convert datetime strings to datetime objects if needed
    coupon['expires_at'] = _parse_datetime(coupon.get('expires_at'))
    coupon['created_at'] = _parse_datetime(coupon.get('created_at'))
    
    return coupon


def create_coupon(code: str, discount_type: str, discount_value: float, min_order_amount: Optional[float],
                  usage_limit: Optional[int], expires_at: Optional[datetime]) -> bool:
    conn = get_db_connection()
    if not conn:
        print("Failed to get database connection in create_coupon")
        return False

    cursor = conn.cursor()
    try:
        # Verify we're connected to the right database
        cursor.execute("SELECT DB_NAME()")
        current_db = cursor.fetchone()[0]
        print(f"Current database: {current_db}")
        
        # Check if table exists (with schema)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'Marketing' AND TABLE_NAME = 'coupons'
        """)
        table_exists = cursor.fetchone()[0] > 0
        print(f"Marketing.coupons table exists: {table_exists}")
        
        if not table_exists:
            print("ERROR: Marketing.coupons table does not exist!")
            return False
        
        print(f"Creating coupon: {code}, type: {discount_type}, value: {discount_value}")
        print(f"  min_order_amount: {min_order_amount}, usage_limit: {usage_limit}, expires_at: {expires_at}")
        
        # Execute the INSERT with schema prefix
        insert_sql = '''
            INSERT INTO Marketing.coupons (code, discount_type, discount_value, min_order_amount, usage_limit, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        params = (code.upper(), discount_type, discount_value, min_order_amount, usage_limit, expires_at)
        
        print(f"Executing INSERT with params: {params}")
        cursor.execute(insert_sql, params)
        
        rows_affected = cursor.rowcount
        print(f"Rows affected by INSERT: {rows_affected}")
        
        # Explicitly commit the transaction
        print("Committing transaction...")
        conn.commit()
        print("[OK] Transaction committed successfully")
        
        # Verify the insert worked by querying the database
        print("Verifying insert...")
        cursor.execute("SELECT COUNT(*) FROM Marketing.coupons WHERE code = ?", (code.upper(),))
        count = cursor.fetchone()[0]
        print(f"[OK] Coupon '{code}' verified in database (count: {count})")
        
        if count == 0:
            print("[WARNING] Insert appeared to succeed but coupon not found in database!")
            return False
        
        return True
    except Exception as e:
        import traceback
        print(f"[ERROR] Error creating coupon: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def update_coupon(coupon_id: int, data: Dict[str, Any]) -> bool:
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            UPDATE Marketing.coupons
            SET code = ?, discount_type = ?, discount_value = ?, min_order_amount = ?, usage_limit = ?, expires_at = ?, is_active = ?
            WHERE coupon_id = ?
            ''',
            (
                data['code'].upper(),
                data['discount_type'],
                data['discount_value'],
                data.get('min_order_amount'),
                data.get('usage_limit'),
                data.get('expires_at'),
                1 if data.get('is_active', True) else 0,
                coupon_id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_coupon_by_code(code: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM Marketing.coupons WHERE code = ?', (code.upper(),))
        row = cursor.fetchone()
        return _row_to_coupon(row) if row else None
    finally:
        cursor.close()
        conn.close()


def get_all_coupons() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM Marketing.coupons ORDER BY created_at DESC')
        return [_row_to_coupon(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def increment_coupon_usage(coupon_id: int) -> None:
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            UPDATE Marketing.coupons
            SET times_used = times_used + 1
            WHERE coupon_id = ?
            ''',
            (coupon_id,),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


