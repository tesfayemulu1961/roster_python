import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify, current_app

ROLES_HIERARCHY = {
    'director': 100,
    'vice_director': 80,
    'supervisor': 70,
    'kg_director': 60,
    'room teacher': 50,
    'subject teacher': 45,
    'student': 20,
    'parent': 15,
}

def generate_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'user_type': user.user_type,
        'exp': datetime.now(timezone.utc) + timedelta(hours=current_app.config['JWT_EXPIRATION_HOURS']),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    return jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            payload = decode_token(token)
            request.current_user_id = payload['user_id']
            request.current_user_type = payload['user_type']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_type = getattr(request, 'current_user_type', None)
            if not user_type:
                return jsonify({'error': 'Authentication required'}), 401

            user_type_lower = user_type.lower()

            for role in allowed_roles:
                if role.lower() in user_type_lower or user_type_lower in role.lower():
                    return f(*args, **kwargs)

            return jsonify({'error': 'Insufficient permissions'}), 403
        return decorated
    return decorator

def get_role_level(user_type):
    user_type_lower = user_type.lower()
    for role, level in ROLES_HIERARCHY.items():
        if role in user_type_lower:
            return level
    return 0

def min_role_required(min_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_type = getattr(request, 'current_user_type', None)
            if not user_type:
                return jsonify({'error': 'Authentication required'}), 401

            user_level = get_role_level(user_type)
            required_level = ROLES_HIERARCHY.get(min_role.lower(), 0)

            if user_level >= required_level:
                return f(*args, **kwargs)

            return jsonify({'error': 'Insufficient permissions'}), 403
        return decorated
    return decorator
