from flask import Blueprint, jsonify, session, redirect, request, render_template
from functools import wraps
import mysql.connector
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
activity_log_bp = Blueprint('activity_log', __name__, url_prefix='/director')

# Database configuration (same as app.py)
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db():
    """Get database connection"""
    return mysql.connector.connect(**db_config)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# ============== NEW FUNCTION 2: REAL-TIME LOG ENTRY ==============
def log_activity(user_id, username, user_type, action, details, ip_address, user_agent):
    """Helper function to insert activity logs - Call this from anywhere in your app"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log (user_id, username, user_type, action, details, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, username, user_type, action, details, ip_address, user_agent))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        return False

@activity_log_bp.route('/activity_log')
@login_required
def view_activity_log():
    """Display activity log page"""
    return render_template('director/activity_log.html')

@activity_log_bp.route('/activity_log/data')
@login_required
def activity_log_data():
    """Return filtered activity logs as JSON"""
    try:
        # Get filter parameters
        user_id = request.args.get('user_id', '').strip()
        username = request.args.get('username', '').strip()
        user_type = request.args.get('user_type', '').strip()
        action = request.args.get('action', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        
        # Build query
        query = "SELECT log_id, user_id, username, user_type, action, details, ip_address, user_agent, created_at FROM activity_log WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = %s"
            params.append(int(user_id))
        
        if username:
            query += " AND username LIKE %s"
            params.append(f'%{username}%')
        
        if user_type:
            query += " AND user_type = %s"
            params.append(user_type)
        
        if action:
            query += " AND action = %s"
            params.append(action)
        
        if date_from:
            query += " AND DATE(created_at) >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND DATE(created_at) <= %s"
            params.append(date_to)
        
        query += " ORDER BY log_id DESC"
        
        # Execute query using MySQL connector
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Format results
        logs = []
        for row in rows:
            logs.append({
                'log_id': row[0],
                'user_id': row[1] if row[1] is not None else 'N/A',
                'username': row[2] if row[2] else 'N/A',
                'user_type': row[3] if row[3] else 'N/A',
                'action': row[4],
                'details': row[5] if row[5] else '',
                'ip_address': row[6] if row[6] else 'N/A',
                'user_agent': row[7] if row[7] else '',
                'created_at': row[8].strftime('%Y-%m-%d %H:%M:%S') if row[8] else ''
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
        
    except Exception as e:
        print(f"Error in activity_log_data: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ============== NEW FUNCTION 1: DELETE OLD LOGS ==============
@activity_log_bp.route('/activity_log/cleanup', methods=['POST'])
@login_required
def cleanup_logs():
    """Delete logs older than 30 days"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Delete logs older than 30 days
        cursor.execute("DELETE FROM activity_log WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)")
        deleted_count = cursor.rowcount
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'deleted': deleted_count,
            'message': f'Successfully deleted {deleted_count} old log entries'
        })
    except Exception as e:
        print(f"Error in cleanup_logs: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500