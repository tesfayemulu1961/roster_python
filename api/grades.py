from flask import Blueprint, request, jsonify
from src.database import db
from src.models import Student, Enrollment, TeacherAssignment, Teacher
from src.jwt_utils import token_required, role_required
from sqlalchemy import func

grade_bp = Blueprint('grades', __name__)

@grade_bp.route('/grades', methods=['GET'])
@token_required
def get_grades():
    grades = db.session.query(
        Student.grade,
        func.count(Student.id).label('student_count')
    ).filter(
        Student.grade.isnot(None),
        Student.status == 1
    ).group_by(Student.grade).order_by(Student.grade).all()

    result = []
    for g in grades:
        sections = db.session.query(
            Student.section,
            func.count(Student.id).label('count')
        ).filter(
            Student.grade == g.grade,
            Student.status == 1
        ).group_by(Student.section).order_by(Student.section).all()

        result.append({
            'grade': g.grade,
            'student_count': g.student_count,
            'sections': [{'section': s.section, 'student_count': s.count} for s in sections],
        })

    return jsonify({'grades': result}), 200

@grade_bp.route('/grades/<grade>/sections', methods=['GET'])
@token_required
def get_sections(grade):
    sections = db.session.query(
        Student.section,
        func.count(Student.id).label('student_count')
    ).filter(
        Student.grade == grade,
        Student.status == 1
    ).group_by(Student.section).order_by(Student.section).all()

    teachers = db.session.query(TeacherAssignment).filter_by(grade=grade).all()

    result = []
    for s in sections:
        section_teachers = [
            t for t in teachers
            if t.section == s.section
        ]
        result.append({
            'section': s.section,
            'student_count': s.student_count,
            'teachers': [
                {
                    'teacher_id': t.teacher_id,
                    'subject': t.subject,
                    'academic_year': t.academic_year,
                }
                for t in section_teachers
            ],
        })

    return jsonify({'grade': grade, 'sections': result}), 200

@grade_bp.route('/sections', methods=['GET'])
@token_required
def get_all_sections():
    grade = request.args.get('grade')

    query = db.session.query(Student.section, Student.grade).filter(
        Student.section.isnot(None),
        Student.status == 1
    )

    if grade:
        query = query.filter(Student.grade == grade)

    sections = query.distinct().order_by(Student.grade, Student.section).all()

    result = []
    for section in sections:
        count = db.session.query(func.count(Student.id)).filter_by(
            grade=section.grade,
            section=section.section,
            status=1
        ).scalar()

        result.append({
            'grade': section.grade,
            'section': section.section,
            'student_count': count,
        })

    return jsonify({'sections': result}), 200

@grade_bp.route('/grades/<grade>', methods=['GET'])
@token_required
def get_grade_detail(grade):
    students = db.session.query(func.count(Student.id)).filter_by(grade=grade, status=1).scalar()

    sections = db.session.query(
        Student.section,
        func.count(Student.id).label('count')
    ).filter(
        Student.grade == grade,
        Student.status == 1
    ).group_by(Student.section).all()

    teachers = db.session.query(TeacherAssignment).filter_by(grade=grade).all()
    unique_teachers = list(set(t.teacher_id for t in teachers))

    return jsonify({
        'grade': grade,
        'total_students': students or 0,
        'sections': [{'section': s.section, 'student_count': s.count} for s in sections],
        'total_teachers': len(unique_teachers),
    }), 200

@grade_bp.route('/academic-years', methods=['GET'])
@token_required
def get_academic_years():
    years = db.session.query(
        Enrollment.academic_year
    ).distinct().order_by(Enrollment.academic_year.desc()).all()

    return jsonify({'academic_years': [y.academic_year for y in years]}), 200
