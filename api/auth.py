from flask import Blueprint, request, jsonify
from src.database import db
from src.models import User, ActivityLog
from src.jwt_utils import generate_token, token_required

auth_bp = Blueprint('auth', __name__)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']

    user = db.session.query(User).filter_by(username=username).first()

    if not user:
        log_activity(None, username, 'login_failed', 'User not found')
        return jsonify({'error': 'Invalid credentials'}), 401

    if user.is_locked():
        return jsonify({'error': f'Account locked. Try again after {user.locked_until.strftime("%Y-%m-%d %H:%M:%S")}'}), 403

    if not user.check_password(password):
        user.record_failed_attempt(MAX_FAILED_ATTEMPTS, LOCKOUT_MINUTES)
        db.session.commit()
        log_activity(user.id, username, 'login_failed', 'Invalid password')
        return jsonify({'error': 'Invalid credentials'}), 401

    user.reset_failed_attempts()
    db.session.commit()

    token = generate_token(user)
    log_activity(user.id, username, 'login_success')

    return jsonify({
        'token': token,
        'user': user.to_dict(),
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    log_activity(request.current_user_id, None, 'logout')
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    user = db.session.get(User, request.current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200

@auth_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_token():
    user = db.session.get(User, request.current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    new_token = generate_token(user)
    return jsonify({'token': new_token}), 200

def log_activity(user_id, username, action, details=None):
    log = ActivityLog(
        user_id=user_id,
        username=username,
        action=action,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
    )
    db.session.add(log)
    db.session.commit()
