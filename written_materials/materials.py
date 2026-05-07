# ==============================================
# Python/Flask equivalent of materials.php
# Original PHP Path: C:\xampp\htdocs\roster_php\written_materials\materials.php
# ==============================================

from flask import Blueprint, jsonify, session, redirect, request
from functools import wraps
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
written_materials_materials = Blueprint('written_materials_materials', __name__, url_prefix='/written_materials')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/materials')
@login_required
def materials_page():
    """Page: Educational Materials - Converted from materials.php"""
    # TODO: Implement the specific functionality
    # Original PHP file: C:\xampp\htdocs\roster_php\written_materials\materials.php
    
    return jsonify({
        "message": "Page: Educational Materials",
        "original_file": "materials.php",
        "status": "under_construction"
    })


# Register this blueprint in main app
# from written_materials_materials import written_materials_materials
# app.register_blueprint(written_materials_materials)
