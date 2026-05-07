# ==============================================
# Python/Flask equivalent of unauthorized.php
# Original PHP Path: C:\xampp\htdocs\roster_php\unauthorized.php
# ==============================================

from flask import Blueprint, jsonify, session, redirect, request
from functools import wraps
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
unauthorized = Blueprint('unauthorized', __name__, url_prefix='/')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/unauthorized')
@login_required
def unauthorized_page():
    """Page: Unauthorized Access - Converted from unauthorized.php"""
    # TODO: Implement the specific functionality
    # Original PHP file: C:\xampp\htdocs\roster_php\unauthorized.php
    
    return jsonify({
        "message": "Page: Unauthorized Access",
        "original_file": "unauthorized.php",
        "status": "under_construction"
    })


# Register this blueprint in main app
# from unauthorized import unauthorized
# app.register_blueprint(unauthorized)
