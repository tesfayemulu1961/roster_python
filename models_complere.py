from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.Enum('director', 'vice director', 'supervisor', 
                                   'KG director', 'student', 'parent', 
                                   'room teacher grade 6th A', 'room teacher grade 6th B',
                                   'room teacher grade 7th A', 'room teacher grade 7th B',
                                   'room teacher grade 8th A', 'room teacher grade 8th B',
                                   'room teacher grade 8th C', 'room teacher grade 8th D',
                                   name='user_type_enum'), nullable=False)
    reference_id = db.Column(db.Integer, nullable=False)
    last_login = db.Column(db.DateTime, default=datetime.now)
    account_status = db.Column(db.Enum('active', 'inactive', 'suspended'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    login_attempts = db.Column(db.Integer, default=0)
    last_failed_attempt = db.Column(db.DateTime)
    
    def get_id(self):
        return str(self.user_id)

class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer, primary_key=True)
    # Add all student fields from PHP

class Teacher(db.Model):
    __tablename__ = 'teacher'
    teacher_id = db.Column(db.Integer, primary_key=True)
    # Add all teacher fields

class Subject(db.Model):
    __tablename__ = 'subject'
    subject_id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100))
    grade_level = db.Column(db.Integer)

class Assessment(db.Model):
    __tablename__ = 'assessment'
    assessment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'))
    score = db.Column(db.Float)
    semester = db.Column(db.Integer)
    academic_year = db.Column(db.String(20))