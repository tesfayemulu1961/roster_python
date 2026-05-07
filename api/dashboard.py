from flask import Blueprint, request, jsonify
from src.database import db
from src.models import User, Student, Teacher, TeacherAssignment, StudentScore, Enrollment, ActivityLog
from src.jwt_utils import token_required, role_required, get_role_level
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/data', methods=['GET'])
@token_required
def get_dashboard_data():
    user_type = getattr(request, 'current_user_type', '')
    user_id = getattr(request, 'current_user_id', None)

    role_level = get_role_level(user_type)

    if role_level >= 100:
        return _director_dashboard()
    elif role_level >= 80:
        return _vice_director_dashboard()
    elif role_level >= 70:
        return _supervisor_dashboard()
    elif 'kg_director' in user_type.lower():
        return _kg_director_dashboard()
    elif 'room teacher' in user_type.lower():
        return _room_teacher_dashboard(user_id, user_type)
    elif 'subject teacher' in user_type.lower():
        return _subject_teacher_dashboard(user_id, user_type)
    elif 'student' in user_type.lower():
        return _student_dashboard(user_id)
    elif 'parent' in user_type.lower():
        return _parent_dashboard(user_id)

    return jsonify({'error': 'Unknown role'}), 403

def _director_dashboard():
    total_students = db.session.query(func.count(Student.id)).filter_by(status=1).scalar()
    total_teachers = db.session.query(func.count(Teacher.id)).filter_by(status=1).scalar()
    total_users = db.session.query(func.count(User.id)).scalar()

    students_by_grade = db.session.query(
        Student.grade,
        func.count(Student.id).label('count')
    ).filter_by(status=1).group_by(Student.grade).order_by(Student.grade).all()

    grade_breakdown = {g.grade: g.count for g in students_by_grade}

    today_logins = db.session.query(func.count(ActivityLog.id)).filter(
        db.func.date(ActivityLog.created_at) == db.func.current_date(),
        ActivityLog.action == 'login_success'
    ).scalar()

    recent_activity = db.session.query(ActivityLog).order_by(
        ActivityLog.created_at.desc()
    ).limit(20).all()

    return jsonify({
        'role': 'director',
        'summary': {
            'total_students': total_students or 0,
            'total_teachers': total_teachers or 0,
            'total_users': total_users or 0,
            'today_logins': today_logins or 0,
        },
        'students_by_grade': grade_breakdown,
        'recent_activity': [a.to_dict() for a in recent_activity],
    }), 200

def _vice_director_dashboard():
    total_students = db.session.query(func.count(Student.id)).filter_by(status=1).scalar()
    total_teachers = db.session.query(func.count(Teacher.id)).filter_by(status=1).scalar()

    students_by_grade = db.session.query(
        Student.grade,
        func.count(Student.id).label('count')
    ).filter_by(status=1).group_by(Student.grade).all()

    recent_logins = db.session.query(
        ActivityLog.username,
        ActivityLog.action,
        ActivityLog.created_at,
        ActivityLog.ip_address
    ).order_by(ActivityLog.created_at.desc()).limit(15).all()

    return jsonify({
        'role': 'vice_director',
        'summary': {
            'total_students': total_students or 0,
            'total_teachers': total_teachers or 0,
        },
        'students_by_grade': {g.grade: g.count for g in students_by_grade},
        'recent_activity': [
            {'username': l.username, 'action': l.action, 'created_at': l.created_at.isoformat(), 'ip_address': l.ip_address}
            for l in recent_logins
        ],
    }), 200

def _supervisor_dashboard():
    assignments = db.session.query(TeacherAssignment).all()

    grades_covered = list(set(a.grade for a in assignments))
    teachers_count = len(set(a.teacher_id for a in assignments))

    return jsonify({
        'role': 'supervisor',
        'summary': {
            'total_assignments': len(assignments),
            'grades_covered': len(grades_covered),
            'teachers_assigned': teachers_count,
        },
        'grades': grades_covered,
        'assignments': [a.to_dict() for a in assignments[:50]],
    }), 200

def _kg_director_dashboard():
    kg_students = db.session.query(func.count(Student.id)).filter(
        Student.grade.ilike('%kg%'),
        Student.status == 1
    ).scalar()

    kg_teachers = db.session.query(func.count(TeacherAssignment.id)).filter(
        TeacherAssignment.grade.ilike('%kg%')
    ).scalar()

    return jsonify({
        'role': 'kg_director',
        'summary': {
            'kg_students': kg_students or 0,
            'kg_teachers': kg_teachers or 0,
        },
    }), 200

def _room_teacher_dashboard(user_id, user_type):
    user = db.session.get(User, user_id)
    teacher = user.teacher if user else None

    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404

    assignments = db.session.query(TeacherAssignment).filter_by(teacher_id=teacher.id).all()

    students = []
    for a in assignments:
        grade_students = db.session.query(Student).filter_by(
            grade=a.grade,
            section=a.section,
            status=1
        ).order_by(Student.name).all()
        students.extend([s.to_dict() for s in grade_students])

    return jsonify({
        'role': 'room_teacher',
        'assignments': [a.to_dict() for a in assignments],
        'students': students,
        'total_students': len(students),
    }), 200

def _subject_teacher_dashboard(user_id, user_type):
    user = db.session.get(User, user_id)
    teacher = user.teacher if user else None

    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404

    assignments = db.session.query(TeacherAssignment).filter_by(teacher_id=teacher.id).all()

    all_students = []
    for a in assignments:
        query = db.session.query(Student).filter_by(status=1)
        if a.grade:
            query = query.filter(Student.grade == a.grade)
        if a.subject:
            query = query.join(StudentScore).filter(StudentScore.subject == a.subject)

        students = query.distinct().order_by(Student.name).all()
        all_students.extend([s.to_dict() for s in students])

    return jsonify({
        'role': 'subject_teacher',
        'assignments': [a.to_dict() for a in assignments],
        'students': list({s['id']: s for s in all_students}.values()),
        'total_students': len(list({s['id']: s for s in all_students}.values())),
    }), 200

def _student_dashboard(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    student = db.session.query(Student).filter(
        db.or_(
            Student.student_id == user.username,
            Student.email == user.email
        )
    ).first()

    if not student:
        return jsonify({'error': 'Student record not found'}), 404

    scores = db.session.query(StudentScore).filter_by(student_id=student.id).all()

    enrollments = db.session.query(Enrollment).filter_by(student_id=student.id).all()

    return jsonify({
        'role': 'student',
        'student': student.to_dict(),
        'scores': [s.to_dict() for s in scores],
        'enrollments': [e.to_dict() for e in enrollments],
    }), 200

def _parent_dashboard(user_id):
    from src.models import Parent

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    parent = db.session.query(Parent).filter(
        db.or_(
            Parent.id == user.username,
            Parent.email == user.email
        )
    ).first()

    if not parent:
        return jsonify({'error': 'Parent record not found'}), 404

    students = db.session.query(Student).filter_by(parent_id=parent.id, status=1).all()

    students_data = []
    for s in students:
        scores = db.session.query(StudentScore).filter_by(student_id=s.id).all()
        students_data.append({
            'student': s.to_dict(),
            'scores': [sc.to_dict() for sc in scores],
        })

    return jsonify({
        'role': 'parent',
        'parent': parent.to_dict(),
        'children': students_data,
    }), 200
