# ==============================================
# Python/Flask equivalent of messages.php
# Original PHP Path: C:\xampp\htdocs\roster_php\js\localhost _ 127.0.0.1 _ test _ enrollment _ phpMyAdmin 5.2.1_files\messages.php
# ==============================================

from flask import Blueprint, jsonify, session, redirect, request
from functools import wraps
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
js_localhost___127_0_0_1___test___enrollment___phpMyAdmin_5_2_1_files_messages = Blueprint('js_localhost___127_0_0_1___test___enrollment___phpMyAdmin_5_2_1_files_messages', __name__, url_prefix='/js/localhost _ 127.0.0.1 _ test _ enrollment _ phpMyAdmin 5.2.1_files')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/messages')
@login_required
def messages_page():
    """Page: Messages - Converted from messages.php"""
    # TODO: Implement the specific functionality
    # Original PHP file: C:\xampp\htdocs\roster_php\js\localhost _ 127.0.0.1 _ test _ enrollment _ phpMyAdmin 5.2.1_files\messages.php
    
    return jsonify({
        "message": "Page: Messages",
        "original_file": "messages.php",
        "status": "under_construction"
    })


# Register this blueprint in main app
# from js_localhost___127_0_0_1___test___enrollment___phpMyAdmin_5_2_1_files_messages import js_localhost___127_0_0_1___test___enrollment___phpMyAdmin_5_2_1_files_messages
# app.register_blueprint(js_localhost___127_0_0_1___test___enrollment___phpMyAdmin_5_2_1_files_messages)
