from flask import Blueprint, request, jsonify
from src.database import db
from src.models import Student, Parent, Enrollment, TeacherAssignment
from src.jwt_utils import token_required

roster_bp = Blueprint('roster', __name__)

@roster_bp.route('/students', methods=['GET'])
@token_required
def get_students():
    grade = request.args.get('grade')
    section = request.args.get('section')
    status = request.args.get('status')

    query = db.session.query(Student)

    if grade:
        query = query.filter_by(grade=grade)
    if section:
        query = query.filter_by(section=section)
    if status is not None:
        query = query.filter_by(status=int(status))

    students = query.order_by(Student.name).all()
    return jsonify({'students': [s.to_dict() for s in students]}), 200

@roster_bp.route('/students/<int:student_id>', methods=['GET'])
@token_required
def get_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    return jsonify({'student': student.to_dict()}), 200

@roster_bp.route('/students', methods=['POST'])
@token_required
def create_student():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('student_id'):
        return jsonify({'error': 'Name and student_id are required'}), 400

    existing = db.session.query(Student).filter_by(student_id=data['student_id']).first()
    if existing:
        return jsonify({'error': 'Student ID already exists'}), 409

    student = Student(
        student_id=data['student_id'],
        name=data['name'],
        parent_id=data.get('parent_id'),
        grade=data.get('grade'),
        section=data.get('section'),
        gender=data.get('gender'),
        phone=data.get('phone'),
        email=data.get('email'),
    )

    db.session.add(student)
    db.session.commit()

    return jsonify({'student': student.to_dict(), 'message': 'Student created'}), 201

@roster_bp.route('/students/<int:student_id>', methods=['PUT'])
@token_required
def update_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    for field in ['name', 'parent_id', 'grade', 'section', 'gender', 'phone', 'email', 'status']:
        if field in data:
            setattr(student, field, data[field])

    db.session.commit()
    return jsonify({'student': student.to_dict(), 'message': 'Student updated'}), 200

@roster_bp.route('/students/<int:student_id>', methods=['DELETE'])
@token_required
def delete_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    db.session.delete(student)
    db.session.commit()
    return jsonify({'message': 'Student deleted'}), 200

@roster_bp.route('/parents', methods=['GET'])
@token_required
def get_parents():
    parents = db.session.query(Parent).order_by(Parent.name).all()
    return jsonify({'parents': [p.to_dict() for p in parents]}), 200

@roster_bp.route('/parents', methods=['POST'])
@token_required
def create_parent():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400

    parent = Parent(
        name=data['name'],
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address'),
    )
    db.session.add(parent)
    db.session.commit()
    return jsonify({'parent': parent.to_dict(), 'message': 'Parent created'}), 201

@roster_bp.route('/enrollments', methods=['GET'])
@token_required
def get_enrollments():
    grade = request.args.get('grade')
    academic_year = request.args.get('academic_year')

    query = db.session.query(Enrollment)
    if grade:
        query = query.filter_by(grade=grade)
    if academic_year:
        query = query.filter_by(academic_year=academic_year)

    enrollments = query.all()
    return jsonify({'enrollments': [e.to_dict() for e in enrollments]}), 200

@roster_bp.route('/enrollments', methods=['POST'])
@token_required
def create_enrollment():
    data = request.get_json()
    if not data or not data.get('student_id') or not data.get('grade') or not data.get('academic_year'):
        return jsonify({'error': 'student_id, grade, and academic_year are required'}), 400

    enrollment = Enrollment(
        student_id=data['student_id'],
        grade=data['grade'],
        section=data.get('section'),
        academic_year=data['academic_year'],
    )
    db.session.add(enrollment)
    db.session.commit()
    return jsonify({'enrollment': enrollment.to_dict(), 'message': 'Enrollment created'}), 201

@roster_bp.route('/assignments', methods=['GET'])
@token_required
def get_assignments():
    teacher_id = request.args.get('teacher_id')
    grade = request.args.get('grade')

    query = db.session.query(TeacherAssignment)
    if teacher_id:
        query = query.filter_by(teacher_id=int(teacher_id))
    if grade:
        query = query.filter_by(grade=grade)

    assignments = query.all()
    return jsonify({'assignments': [a.to_dict() for a in assignments]}), 200

@roster_bp.route('/assignments', methods=['POST'])
@token_required
def create_assignment():
    data = request.get_json()
    if not data or not data.get('teacher_id') or not data.get('grade') or not data.get('academic_year'):
        return jsonify({'error': 'teacher_id, grade, and academic_year are required'}), 400

    assignment = TeacherAssignment(
        teacher_id=data['teacher_id'],
        grade=data['grade'],
        section=data.get('section'),
        subject=data.get('subject'),
        academic_year=data['academic_year'],
    )
    db.session.add(assignment)
    db.session.commit()
    return jsonify({'assignment': assignment.to_dict(), 'message': 'Assignment created'}), 201
