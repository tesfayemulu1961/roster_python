# ==============================================
# Python/Flask equivalent of subject_helper.php
# Original PHP Path: C:\xampp\htdocs\roster_php\helpers\subject_helper.php
# ==============================================

from flask import Blueprint, jsonify, session, redirect, request
from functools import wraps
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
helpers_subject_helper = Blueprint('helpers_subject_helper', __name__, url_prefix='/helpers')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/subject_helper')
@login_required
def subject_helper_page():
    """Page: Subject Helper - Converted from subject_helper.php"""
    # TODO: Implement the specific functionality
    # Original PHP file: C:\xampp\htdocs\roster_php\helpers\subject_helper.php
    
    return jsonify({
        "message": "Page: Subject Helper",
        "original_file": "subject_helper.php",
        "status": "under_construction"
    })


# Register this blueprint in main app
# from helpers_subject_helper import helpers_subject_helper
# app.register_blueprint(helpers_subject_helper)
