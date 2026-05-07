# ==============================================
# Python/Flask equivalent of insert_subject.php
# Original PHP Path: C:\xampp\htdocs\roster_php\vice_director\insert_subject.php
# ==============================================

from flask import Blueprint, jsonify, session, redirect, request
from functools import wraps
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
vice_director_insert_subject = Blueprint('vice_director_insert_subject', __name__, url_prefix='/vice_director')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/insert_subject')
@login_required
def insert_subject_page():
    """Page: Add New Subject - Converted from insert_subject.php"""
    # TODO: Implement the specific functionality
    # Original PHP file: C:\xampp\htdocs\roster_php\vice_director\insert_subject.php
    
    return jsonify({
        "message": "Page: Add New Subject",
        "original_file": "insert_subject.php",
        "status": "under_construction"
    })


# Register this blueprint in main app
# from vice_director_insert_subject import vice_director_insert_subject
# app.register_blueprint(vice_director_insert_subject)
