from flask import Blueprint, request, jsonify
from src.database import db
from src.models import Teacher, User, TeacherAssignment
from src.jwt_utils import token_required, role_required
from sqlalchemy import func

teacher_bp = Blueprint('teachers', __name__)

@teacher_bp.route('/teachers', methods=['GET'])
@token_required
def get_teachers():
    status = request.args.get('status')
    user_type = request.args.get('user_type')
    grade = request.args.get('grade')
    section = request.args.get('section')
    subject = request.args.get('subject')

    query = db.session.query(Teacher)

    if status is not None:
        query = query.filter_by(status=int(status))

    if grade or section or subject:
        query = query.join(TeacherAssignment)
        if grade:
            query = query.filter(TeacherAssignment.grade == grade)
        if section:
            query = query.filter(TeacherAssignment.section == section)
        if subject:
            query = query.filter(TeacherAssignment.subject == subject)

    query = query.order_by(Teacher.name)
    teachers = query.all()

    result = []
    for t in teachers:
        data = t.to_dict()
        user = db.session.get(User, t.user_id) if t.user_id else None
        if user:
            data['username'] = user.username
            data['user_type'] = user.user_type
        result.append(data)

    return jsonify({'teachers': result}), 200

@teacher_bp.route('/teachers/<int:teacher_id>', methods=['GET'])
@token_required
def get_teacher(teacher_id):
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return jsonify({'error': 'Teacher not found'}), 404

    data = teacher.to_dict()
    user = db.session.get(User, teacher.user_id) if teacher.user_id else None
    if user:
        data['user'] = user.to_dict()

    assignments = db.session.query(TeacherAssignment).filter_by(teacher_id=teacher_id).all()
    data['assignments'] = [a.to_dict() for a in assignments]

    return jsonify({'teacher': data}), 200

@teacher_bp.route('/teachers', methods=['POST'])
@token_required
@role_required(['director', 'vice_director'])
def create_teacher():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400

    teacher = Teacher(
        name=data['name'],
        phone=data.get('phone'),
        email=data.get('email'),
        status=data.get('status', 1),
    )

    if data.get('username') and data.get('password'):
        existing_user = db.session.query(User).filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 409

        user = User(
            username=data['username'],
            user_type=data.get('user_type', 'subject teacher'),
            email=data.get('email'),
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.flush()
        teacher.user_id = user.id

    db.session.add(teacher)
    db.session.commit()

    result = teacher.to_dict()
    if teacher.user_id:
        user = db.session.get(User, teacher.user_id)
        if user:
            result['username'] = user.username
            result['user_type'] = user.user_type

    return jsonify({'teacher': result, 'message': 'Teacher created'}), 201

@teacher_bp.route('/teachers/<int:teacher_id>', methods=['PUT'])
@token_required
@role_required(['director', 'vice_director'])
def update_teacher(teacher_id):
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return jsonify({'error': 'Teacher not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    for field in ['name', 'phone', 'email', 'status']:
        if field in data:
            setattr(teacher, field, data[field])

    if teacher.user_id and 'password' in data:
        user = db.session.get(User, teacher.user_id)
        if user:
            user.set_password(data['password'])

    db.session.commit()
    return jsonify({'teacher': teacher.to_dict(), 'message': 'Teacher updated'}), 200

@teacher_bp.route('/teachers/<int:teacher_id>', methods=['DELETE'])
@token_required
@role_required(['director'])
def delete_teacher(teacher_id):
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return jsonify({'error': 'Teacher not found'}), 404

    if teacher.user_id:
        user = db.session.get(User, teacher.user_id)
        if user:
            db.session.delete(user)

    db.session.delete(teacher)
    db.session.commit()
    return jsonify({'message': 'Teacher deleted'}), 200

@teacher_bp.route('/teachers/<int:teacher_id>/assignments', methods=['GET'])
@token_required
def get_teacher_assignments(teacher_id):
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return jsonify({'error': 'Teacher not found'}), 404

    assignments = db.session.query(TeacherAssignment).filter_by(teacher_id=teacher_id).all()
    return jsonify({'assignments': [a.to_dict() for a in assignments]}), 200

@teacher_bp.route('/teachers/<int:teacher_id>/assignments', methods=['POST'])
@token_required
@role_required(['director', 'vice_director'])
def assign_teacher(teacher_id):
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return jsonify({'error': 'Teacher not found'}), 404

    data = request.get_json()
    if not data or not data.get('grade') or not data.get('academic_year'):
        return jsonify({'error': 'Grade and academic_year are required'}), 400

    assignment = TeacherAssignment(
        teacher_id=teacher_id,
        grade=data['grade'],
        section=data.get('section'),
        subject=data.get('subject'),
        academic_year=data['academic_year'],
    )
    db.session.add(assignment)
    db.session.commit()

    if teacher.user_id:
        user = db.session.get(User, teacher.user_id)
        if user and data.get('user_type'):
            user.user_type = data['user_type']
            db.session.commit()

    return jsonify({'assignment': assignment.to_dict(), 'message': 'Teacher assigned'}), 201

@teacher_bp.route('/teachers/stats', methods=['GET'])
@token_required
@role_required(['director', 'vice_director', 'supervisor'])
def get_teacher_stats():
    total = db.session.query(func.count(Teacher.id)).scalar()
    active = db.session.query(func.count(Teacher.id)).filter_by(status=1).scalar()
    inactive = db.session.query(func.count(Teacher.id)).filter_by(status=0).scalar()

    assignments = db.session.query(
        TeacherAssignment.grade,
        func.count(TeacherAssignment.id).label('count')
    ).group_by(TeacherAssignment.grade).all()

    grade_distribution = {a.grade: a.count for a in assignments}

    return jsonify({
        'total': total,
        'active': active,
        'inactive': inactive,
        'by_grade': grade_distribution,
    }), 200
