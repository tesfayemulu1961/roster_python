from flask import Blueprint, request, jsonify
from src.database import db
from src.models import User, Teacher, ActivityLog
from src.jwt_utils import token_required, role_required, min_role_required
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@token_required
@min_role_required('vice_director')
def get_users():
    user_type = request.args.get('user_type')
    status = request.args.get('status')
    search = request.args.get('search')

    query = db.session.query(User)

    if user_type:
        query = query.filter(User.user_type.ilike(f'%{user_type}%'))
    if status is not None:
        query = query.filter_by(status=int(status))
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )

    users = query.order_by(User.username).all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
@min_role_required('vice_director')
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = user.to_dict()
    if user.teacher:
        data['teacher'] = user.teacher.to_dict()

    return jsonify({'user': data}), 200

@admin_bp.route('/users', methods=['POST'])
@token_required
@min_role_required('director')
def create_user():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password') or not data.get('user_type'):
        return jsonify({'error': 'Username, password, and user_type are required'}), 400

    existing = db.session.query(User).filter_by(username=data['username']).first()
    if existing:
        return jsonify({'error': 'Username already exists'}), 409

    user = User(
        username=data['username'],
        user_type=data['user_type'],
        email=data.get('email'),
        phone=data.get('phone'),
        status=data.get('status', 1),
    )
    user.set_password(data['password'])

    if data.get('teacher_id'):
        teacher = db.session.get(Teacher, data['teacher_id'])
        if teacher:
            teacher.user_id = user.id

    db.session.add(user)
    db.session.commit()
    return jsonify({'user': user.to_dict(), 'message': 'User created'}), 201

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
@min_role_required('director')
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'username' in data and data['username'] != user.username:
        existing = db.session.query(User).filter_by(username=data['username']).first()
        if existing:
            return jsonify({'error': 'Username already exists'}), 409
        user.username = data['username']

    for field in ['user_type', 'email', 'phone', 'status']:
        if field in data:
            setattr(user, field, data[field])

    if 'password' in data:
        user.set_password(data['password'])

    db.session.commit()
    return jsonify({'user': user.to_dict(), 'message': 'User updated'}), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@min_role_required('director')
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.id == request.current_user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'}), 200

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@token_required
@min_role_required('director')
def toggle_user_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.status = 0 if user.status == 1 else 1
    db.session.commit()
    return jsonify({'user': user.to_dict(), 'message': f'User {"disabled" if user.status == 0 else "enabled"}'}), 200

@admin_bp.route('/activity-log', methods=['GET'])
@token_required
@min_role_required('vice_director')
def get_activity_log():
    user_id = request.args.get('user_id')
    action = request.args.get('action')
    limit = request.args.get('limit', 100, type=int)

    query = db.session.query(ActivityLog)

    if user_id:
        query = query.filter_by(user_id=int(user_id))
    if action:
        query = query.filter_by(action=action)

    logs = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    return jsonify({'logs': [l.to_dict() for l in logs]}), 200

@admin_bp.route('/stats', methods=['GET'])
@token_required
@min_role_required('vice_director')
def get_system_stats():
    total_users = db.session.query(func.count(User.id)).scalar()
    active_users = db.session.query(func.count(User.id)).filter_by(status=1).scalar()
    total_students = db.session.query(func.count(User.id)).filter(User.user_type.like('%student%')).scalar()
    total_teachers = db.session.query(func.count(User.id)).filter(User.user_type.like('%teacher%')).scalar()
    total_logins = db.session.query(func.count(ActivityLog.id)).filter_by(action='login_success').scalar()
    total_failed = db.session.query(func.count(ActivityLog.id)).filter_by(action='login_failed').scalar()

    recent_logins = db.session.query(
        ActivityLog.username,
        ActivityLog.created_at,
        ActivityLog.ip_address
    ).filter_by(action='login_success').order_by(ActivityLog.created_at.desc()).limit(10).all()

    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_logins': total_logins,
        'total_failed_logins': total_failed,
        'recent_logins': [
            {'username': l.username, 'created_at': l.created_at.isoformat(), 'ip_address': l.ip_address}
            for l in recent_logins
        ],
    }), 200
