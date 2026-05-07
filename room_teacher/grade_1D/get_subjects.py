# ==============================================
# Python/Flask equivalent of get_subjects.php
# Original PHP Path: C:\xampp\htdocs\roster_php\room_teacher\grade_1D\get_subjects.php
# ==============================================

from flask import Blueprint, jsonify, session, redirect, request
from functools import wraps
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
room_teacher_grade_1D_get_subjects = Blueprint('room_teacher_grade_1D_get_subjects', __name__, url_prefix='/room_teacher/grade_1D')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/get_subjects')
@login_required
def get_subjects_page():
    """Page: Get Subjects - Converted from get_subjects.php"""
    # TODO: Implement the specific functionality
    # Original PHP file: C:\xampp\htdocs\roster_php\room_teacher\grade_1D\get_subjects.php
    
    return jsonify({
        "message": "Page: Get Subjects",
        "original_file": "get_subjects.php",
        "status": "under_construction"
    })


# Register this blueprint in main app
# from room_teacher_grade_1D_get_subjects import room_teacher_grade_1D_get_subjects
# app.register_blueprint(room_teacher_grade_1D_get_subjects)
