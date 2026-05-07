from functools import wraps
from flask import session, redirect, url_for, request
from datetime import datetime, timedelta
import mysql.connector

# Session configuration (equivalent to PHP session settings)
def configure_session(app):
    """Configure Flask session settings similar to PHP"""
    app.config['SESSION_COOKIE_NAME'] = 'SCHOOLSESSID'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # 86400 seconds
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Database configuration (import from your main app or define here)
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db():
    return mysql.connector.connect(**db_config)

# Login required decorator (replaces the auth check)
def login_required(f):
    """
    Decorator to check if user is logged in.
    Equivalent to checking if session['user_id'] exists in PHP.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip auth check for login page
        if request.endpoint == 'login':
            return f(*args, **kwargs)
        
        # Check if user is logged in
        if 'user_id' not in session:
            session['error'] = "Please login to access this page"
            return redirect(url_for('login'))
        
        # Verify session data is consistent (required fields)
        required_fields = ['user_id', 'username', 'user_type', 'reference_id']
        for field in required_fields:
            if field not in session:
                session.clear()
                session['error'] = "Session data corrupted. Please login again."
                return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

# Role-based access decorator
def role_required(allowed_roles):
    """
    Decorator to check if user has allowed role.
    Equivalent to checking user_type against allowed types in PHP.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_type' not in session:
                session.clear()
                return redirect(url_for('login'))
            
            if session['user_type'] not in allowed_roles:
                return redirect(url_for('unauthorized'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Database verification decorator (verifies user still exists and is active)
def verify_db_user(f):
    """
    Decorator to verify user exists and is active in database.
    Equivalent to the database verification in PHP.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'username' not in session:
            session.clear()
            return redirect(url_for('login'))
        
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 1 FROM users 
                WHERE user_id = %s 
                AND username = %s 
                AND account_status = 'active'
            """, (session['user_id'], session['username']))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                session.clear()
                return redirect(url_for('login'))
                
        except Exception as e:
            print(f"Database verification error: {e}")
            session.clear()
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

# Complete authentication decorator (combines all checks)
def auth_required(allowed_roles=None):
    """
    Complete authentication decorator that combines:
    - Login check
    - Session data validation
    - Database verification
    - Role-based access (optional)
    """
    def decorator(f):
        @wraps(f)
        @login_required
        @verify_db_user
        def decorated_function(*args, **kwargs):
            if allowed_roles and session.get('user_type') not in allowed_roles:
                return redirect(url_for('unauthorized'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Helper function to get current user info
def get_current_user():
    """Get current user information from session"""
    if 'user_id' not in session:
        return None
    
    return {
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'user_type': session.get('user_type'),
        'reference_id': session.get('reference_id'),
        'display_name': session.get('display_name', session.get('username'))
    }

# Helper function to check if user is logged in
def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session

# Helper function to check user role
def has_role(role):
    """Check if current user has specific role"""
    return session.get('user_type') == role

# Helper function to check if user has any of the allowed roles
def has_any_role(roles):
    """Check if current user has any of the allowed roles"""
    return session.get('user_type') in roles

# Activity logger (equivalent to recordActivity in PHP)
def record_activity(user_id, username, user_type, action, details=None, ip_address=None):
    """Record user activity in the database"""
    try:
        from flask import request
        if ip_address is None:
            ip_address = request.remote_addr
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log (user_id, username, action, details, ip_address, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (user_id, username, action, details, ip_address))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error recording activity: {e}")

# Example usage in your routes:
"""
from auth_check import auth_required, role_required, get_current_user

# Protect director dashboard - only directors can access
@app.route('/director/dashboard')
@auth_required(allowed_roles=['director'])
def director_dashboard():
    current_user = get_current_user()
    return f"Welcome {current_user['username']} to Director Dashboard"

# Protect teacher dashboard - only teachers can access
@app.route('/teacher/dashboard')
@auth_required(allowed_roles=['room teacher grade 7th A', 'subject teacher grade 7th Amharic'])
def teacher_dashboard():
    return "Teacher Dashboard"

# Simple login required
@app.route('/profile')
@login_required
def profile():
    return "Your profile"

# Role-specific route using role_required
@app.route('/admin')
@role_required(['director', 'supervisor'])
def admin_panel():
    return "Admin Panel"
"""