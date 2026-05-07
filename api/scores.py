from flask import Blueprint, request, jsonify
from src.database import db
from src.models import StudentScore, Student
from src.jwt_utils import token_required, role_required
from sqlalchemy import func, case

score_bp = Blueprint('scores', __name__)

def calculate_grade(score):
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'

@score_bp.route('/scores', methods=['GET'])
@token_required
def get_scores():
    student_id = request.args.get('student_id')
    subject = request.args.get('subject')
    academic_year = request.args.get('academic_year')
    term = request.args.get('term')
    grade = request.args.get('grade')

    query = db.session.query(StudentScore).join(Student)

    if student_id:
        query = query.filter(StudentScore.student_id == int(student_id))
    if subject:
        query = query.filter(StudentScore.subject == subject)
    if academic_year:
        query = query.filter(StudentScore.academic_year == academic_year)
    if term:
        query = query.filter(StudentScore.term == term)
    if grade:
        query = query.filter(Student.grade == grade)

    scores = query.order_by(StudentScore.student_id, StudentScore.subject).all()
    return jsonify({'scores': [s.to_dict() for s in scores]}), 200

@score_bp.route('/scores/<int:score_id>', methods=['GET'])
@token_required
def get_score(score_id):
    score = db.session.get(StudentScore, score_id)
    if not score:
        return jsonify({'error': 'Score not found'}), 404
    return jsonify({'score': score.to_dict()}), 200

@score_bp.route('/scores', methods=['POST'])
@token_required
@role_required(['director', 'vice_director', 'supervisor', 'subject teacher', 'room teacher'])
def create_score():
    data = request.get_json()
    if not data or not data.get('student_id') or not data.get('subject') or data.get('score') is None:
        return jsonify({'error': 'student_id, subject, and score are required'}), 400

    student = db.session.get(Student, data['student_id'])
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    score_value = float(data['score'])
    if score_value < 0 or score_value > 100:
        return jsonify({'error': 'Score must be between 0 and 100'}), 400

    existing = db.session.query(StudentScore).filter_by(
        student_id=data['student_id'],
        subject=data['subject'],
        academic_year=data.get('academic_year', ''),
        term=data.get('term', ''),
    ).first()

    if existing:
        existing.score = score_value
        existing.grade = data.get('grade') or calculate_grade(score_value)
        db.session.commit()
        return jsonify({'score': existing.to_dict(), 'message': 'Score updated'}), 200

    score = StudentScore(
        student_id=data['student_id'],
        subject=data['subject'],
        score=score_value,
        grade=data.get('grade') or calculate_grade(score_value),
        academic_year=data.get('academic_year', ''),
        term=data.get('term', ''),
    )
    db.session.add(score)
    db.session.commit()
    return jsonify({'score': score.to_dict(), 'message': 'Score created'}), 201

@score_bp.route('/scores/<int:score_id>', methods=['PUT'])
@token_required
@role_required(['director', 'vice_director', 'supervisor'])
def update_score(score_id):
    score = db.session.get(StudentScore, score_id)
    if not score:
        return jsonify({'error': 'Score not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'score' in data:
        score_value = float(data['score'])
        if score_value < 0 or score_value > 100:
            return jsonify({'error': 'Score must be between 0 and 100'}), 400
        score.score = score_value
        score.grade = data.get('grade') or calculate_grade(score_value)

    for field in ['subject', 'academic_year', 'term', 'grade']:
        if field in data:
            setattr(score, field, data[field])

    db.session.commit()
    return jsonify({'score': score.to_dict(), 'message': 'Score updated'}), 200

@score_bp.route('/scores/<int:score_id>', methods=['DELETE'])
@token_required
@role_required(['director', 'vice_director'])
def delete_score(score_id):
    score = db.session.get(StudentScore, score_id)
    if not score:
        return jsonify({'error': 'Score not found'}), 404

    db.session.delete(score)
    db.session.commit()
    return jsonify({'message': 'Score deleted'}), 200

@score_bp.route('/scores/bulk', methods=['POST'])
@token_required
@role_required(['director', 'vice_director', 'supervisor', 'subject teacher', 'room teacher'])
def bulk_create_scores():
    data = request.get_json()
    if not data or 'scores' not in data:
        return jsonify({'error': 'Scores array is required'}), 400

    created = []
    updated = []
    errors = []

    for entry in data['scores']:
        if not entry.get('student_id') or not entry.get('subject') or entry.get('score') is None:
            errors.append({'entry': entry, 'error': 'Missing required fields'})
            continue

        score_value = float(entry['score'])
        if score_value < 0 or score_value > 100:
            errors.append({'entry': entry, 'error': 'Score must be between 0 and 100'})
            continue

        existing = db.session.query(StudentScore).filter_by(
            student_id=entry['student_id'],
            subject=entry['subject'],
            academic_year=entry.get('academic_year', ''),
            term=entry.get('term', ''),
        ).first()

        if existing:
            existing.score = score_value
            existing.grade = entry.get('grade') or calculate_grade(score_value)
            updated.append(existing.to_dict())
        else:
            score = StudentScore(
                student_id=entry['student_id'],
                subject=entry['subject'],
                score=score_value,
                grade=entry.get('grade') or calculate_grade(score_value),
                academic_year=entry.get('academic_year', ''),
                term=entry.get('term', ''),
            )
            db.session.add(score)
            created.append(score.to_dict())

    db.session.commit()
    return jsonify({
        'created': created,
        'updated': updated,
        'errors': errors,
        'message': f'{len(created)} created, {len(updated)} updated, {len(errors)} errors',
    }), 200

@score_bp.route('/scores/student/<int:student_id>/report', methods=['GET'])
@token_required
def get_student_report(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    academic_year = request.args.get('academic_year')
    term = request.args.get('term')

    query = db.session.query(StudentScore).filter_by(student_id=student_id)
    if academic_year:
        query = query.filter_by(academic_year=academic_year)
    if term:
        query = query.filter_by(term=term)

    scores = query.all()

    if not scores:
        return jsonify({'student': student.to_dict(), 'scores': [], 'average': None}), 200

    total = sum(s.score for s in scores)
    average = total / len(scores)

    subject_summary = {}
    for s in scores:
        if s.subject not in subject_summary:
            subject_summary[s.subject] = []
        subject_summary[s.subject].append(s.score)

    subject_averages = {
        subj: sum(vals) / len(vals)
        for subj, vals in subject_summary.items()
    }

    return jsonify({
        'student': student.to_dict(),
        'scores': [s.to_dict() for s in scores],
        'average': round(average, 2),
        'total': len(scores),
        'subject_averages': subject_averages,
    }), 200

@score_bp.route('/scores/summary', methods=['GET'])
@token_required
@role_required(['director', 'vice_director', 'supervisor'])
def get_score_summary():
    grade = request.args.get('grade')
    section = request.args.get('section')
    academic_year = request.args.get('academic_year')
    term = request.args.get('term')

    query = db.session.query(StudentScore).join(Student)

    if academic_year:
        query = query.filter(StudentScore.academic_year == academic_year)
    if term:
        query = query.filter(StudentScore.term == term)
    if grade:
        query = query.filter(Student.grade == grade)
    if section:
        query = query.filter(Student.section == section)

    scores = query.all()

    if not scores:
        return jsonify({'total': 0, 'average': None, 'grade_distribution': {}}), 200

    total = len(scores)
    average = sum(s.score for s in scores) / total

    grade_distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    for s in scores:
        grade_letter = s.grade or calculate_grade(s.score)
        if grade_letter in grade_distribution:
            grade_distribution[grade_letter] += 1

    return jsonify({
        'total': total,
        'average': round(average, 2),
        'highest': max(s.score for s in scores),
        'lowest': min(s.score for s in scores),
        'grade_distribution': grade_distribution,
    }), 200
