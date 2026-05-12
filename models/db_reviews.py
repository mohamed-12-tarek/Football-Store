from typing import List, Dict, Any, Optional, Tuple

from models.db import get_db_connection


def save_review(product_id: int, user_id: int, rating: int, title: Optional[str], content: str) -> bool:
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO Products.product_reviews (product_id, user_id, rating, title, content)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (product_id, user_id, rating, title, content),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_review_stats(product_id: int) -> Dict[str, float]:
    conn = get_db_connection()
    if not conn:
        return {'average': 0.0, 'count': 0}

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT 
                ISNULL(AVG(CAST(rating AS FLOAT)), 0),
                COUNT(*)
            FROM Products.product_reviews
            WHERE product_id = ? AND status = 'Approved'
            ''',
            (product_id,),
        )
        row = cursor.fetchone()
        return {'average': float(row[0] or 0), 'count': int(row[1] or 0)}
    finally:
        cursor.close()
        conn.close()


def get_reviews_by_product(product_id: int, only_approved: bool = True) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        status_clause = 'AND pr.status = \'Approved\'' if only_approved else ''
        query = f'''
            SELECT pr.review_id,
                   pr.rating,
                   pr.title,
                   pr.content,
                   pr.status,
                   pr.created_at,
                   u.username
            FROM Products.product_reviews pr
            JOIN Users.users u ON pr.user_id = u.user_id
            WHERE pr.product_id = ?
            {status_clause}
            ORDER BY pr.created_at DESC
        '''
        cursor.execute(query, (product_id,))
        rows = cursor.fetchall()
        return [
            {
                'review_id': row[0],
                'rating': row[1],
                'title': row[2],
                'content': row[3],
                'status': row[4],
                'created_at': row[5],
                'username': row[6],
            }
            for row in rows
        ]
    finally:
        cursor.close()
        conn.close()


def get_reviews_for_admin(status: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        query = '''
            SELECT pr.review_id,
                   p.name,
                   u.username,
                   pr.rating,
                   pr.title,
                   pr.content,
                   pr.status,
                   pr.created_at
            FROM Products.product_reviews pr
            JOIN Products.products p ON pr.product_id = p.product_id
            JOIN Users.users u ON pr.user_id = u.user_id
        '''
        params: Tuple[Any, ...] = ()
        if status:
            query += ' WHERE pr.status = ?'
            params = (status,)
        query += ' ORDER BY pr.created_at DESC'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [
            {
                'review_id': row[0],
                'product_name': row[1],
                'username': row[2],
                'rating': row[3],
                'title': row[4],
                'content': row[5],
                'status': row[6],
                'created_at': row[7],
            }
            for row in rows
        ]
    finally:
        cursor.close()
        conn.close()


def update_review_status(review_id: int, status: str) -> bool:
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            UPDATE Products.product_reviews
            SET status = ?, updated_at = GETDATE()
            WHERE review_id = ?
            ''',
            (status, review_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def delete_review(review_id: int) -> bool:
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM Products.product_reviews WHERE review_id = ?', (review_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


