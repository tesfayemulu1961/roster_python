# ==============================================
# Python/Flask equivalent of view_subject.php
# Original PHP Path: C:\xampp\htdocs\roster_php\vice_director\view_subject.php
# ==============================================

from flask import Blueprint, jsonify, session, redirect, request
from functools import wraps
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
vice_director_view_subject = Blueprint('vice_director_view_subject', __name__, url_prefix='/vice_director')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/view_subject')
@login_required
def view_subject_page():
    """Page: View Subjects - Converted from view_subject.php"""
    # TODO: Implement the specific functionality
    # Original PHP file: C:\xampp\htdocs\roster_php\vice_director\view_subject.php
    
    return jsonify({
        "message": "Page: View Subjects",
        "original_file": "view_subject.php",
        "status": "under_construction"
    })


# Register this blueprint in main app
# from vice_director_view_subject import vice_director_view_subject
# app.register_blueprint(vice_director_view_subject)
