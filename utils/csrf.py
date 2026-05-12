from functools import wraps
import secrets
from flask import session, request, jsonify, abort

CSRF_TOKEN_LENGTH = 32

def generate_csrf_token():
    """Generate a CSRF token and store in session"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(CSRF_TOKEN_LENGTH)
    return session['csrf_token']

def validate_csrf_token():
    """Validate CSRF token from request"""
    token = session.get('csrf_token')
    if not token:
        return False

    request_token = None
    if request.is_json:
        request_token = request.json.get('csrf_token')
    else:
        request_token = request.form.get('csrf_token')

    if not request_token:
        request_token = request.headers.get('X-CSRF-Token')

    return token == request_token

def csrf_protect(f):
    """Decorator to protect routes against CSRF"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            if not validate_csrf_token():
                abort(403)
        return f(*args, **kwargs)
    return decorated_function

def csrf_token_required(f):
    """Decorator that requires a valid CSRF token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_csrf_token():
            if request.is_json:
                return jsonify({'success': False, 'message': 'Invalid or missing CSRF token'}), 403
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
