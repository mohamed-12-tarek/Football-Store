from datetime import datetime
from typing import List, Optional, Dict, Any

from models.db import get_db_connection


def _parse_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(value)
        except (ValueError, AttributeError):
            return value
    return value


def _row_to_dict(row) -> Optional[Dict[str, Any]]:
    if not row:
        return None

    keys = [
        'message_id',
        'user_id',
        'name',
        'email',
        'subject',
        'message',
        'response',
        'status',
        'created_at',
        'replied_at',
    ]
    record = {key: value for key, value in zip(keys, row)}
    record['created_at'] = _parse_datetime(record.get('created_at'))
    record['replied_at'] = _parse_datetime(record.get('replied_at'))
    return record


def save_user_message(name: str, email: str, subject: str, message: str) -> bool:
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO Users.user_messages (name, email, subject, message)
            VALUES (?, ?, ?, ?)
            ''',
            (name, email, subject, message),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_all_messages() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT message_id, user_id, name, email, subject, message, response, status, created_at, replied_at
            FROM Users.user_messages
            ORDER BY created_at DESC
            '''
        )
        rows = cursor.fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()


def get_message_by_id(message_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            SELECT message_id, user_id, name, email, subject, message, response, status, created_at, replied_at
            FROM Users.user_messages
            WHERE message_id = ?
            ''',
            (message_id,),
        )
        row = cursor.fetchone()
        return _row_to_dict(row)
    finally:
        cursor.close()
        conn.close()


def update_message_response(
    message_id: int,
    response_text: str,
    status: str = 'Replied',
) -> bool:
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            UPDATE Users.user_messages
            SET response = ?, status = ?, replied_at = GETDATE()
            WHERE message_id = ?
            ''',
            (response_text, status, message_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

