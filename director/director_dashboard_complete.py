from flask import Blueprint, render_template, session, redirect, url_for
from models import db, User, Student, Teacher, Subject

director_bp = Blueprint('director', __name__, url_prefix='/director')

@director_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('user_type') != 'director':
        return redirect(url_for('login'))
    
    # Get real statistics from database
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_subjects = Subject.query.count()
    
    return render_template('director/dashboard.html',
                         username=session['username'],
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_subjects=total_subjects)

@director_bp.route('/students')
def manage_students():
    students = Student.query.all()
    return render_template('director/students.html', students=students)

@director_bp.route('/teachers')
def manage_teachers():
    teachers = Teacher.query.all()
    return render_template('director/teachers.html', teachers=teachers)