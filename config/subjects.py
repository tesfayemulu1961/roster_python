# ==============================================
# Python/Flask equivalent of subjects.php
# Original PHP Path: C:\xampp\htdocs\roster_php\config\subjects.php
# ==============================================

from flask import Blueprint, jsonify, session, redirect, request
from functools import wraps
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
config_subjects = Blueprint('config_subjects', __name__, url_prefix='/config')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/subjects')
@login_required
def subjects_page():
    """Page: Subjects - Converted from subjects.php"""
    # TODO: Implement the specific functionality
    # Original PHP file: C:\xampp\htdocs\roster_php\config\subjects.php
    
    return jsonify({
        "message": "Page: Subjects",
        "original_file": "subjects.php",
        "status": "under_construction"
    })


# Register this blueprint in main app
# from config_subjects import config_subjects
# app.register_blueprint(config_subjects)
