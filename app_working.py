from flask import Flask, render_template_string, session, redirect, request
from datetime import datetime
import mysql.connector
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db():
    return mysql.connector.connect(**db_config)

# ============== IMPORT DIRECTOR DASHBOARD BLUEPRINT ==============
try:
    from director.director_dashboard import director_dashboard_bp
    app.register_blueprint(director_dashboard_bp)
    print("✅ Director Dashboard Blueprint registered successfully")
    print("   URL: /director/director_dashboard")
except Exception as e:
    print(f"❌ Error registering director dashboard: {e}")

# ============== LOGIN TEMPLATE ==============
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>School Management System - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            width: 400px;
        }
        h2 { text-align: center; color: #333; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }
        button:hover { opacity: 0.9; }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>🏫 School Management System</h2>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Login</button>
        </form>
        <div style="margin-top: 20px; font-size: 12px; text-align: center; color: #666;">
            <p>Test: director001 (any password)</p>
        </div>
    </div>
</body>
</html>
'''

# ============== DASHBOARD ROUTE MAPPING ==============
def get_dashboard_route(user_type):
    """Return the appropriate dashboard route based on user type"""
    
    if user_type == 'director':
        return '/director/director_dashboard'
    else:
        return '/dashboard'

# ============== LOGIN ROUTE ==============
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template_string(LOGIN_TEMPLATE, error="Please enter both username and password.")
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT user_id, username, user_type, reference_id, account_status 
                FROM users 
                WHERE username = %s LIMIT 1
            """, (username,))
            user = cursor.fetchone()
            
            if user and user['account_status'] == 'active':
                # For testing - accept any password
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['user_type'] = user['user_type']
                session['reference_id'] = user['reference_id']
                session['logged_in'] = True
                
                # Update last login
                cursor.execute("UPDATE users SET last_login = NOW() WHERE user_id = %s", (user['user_id'],))
                conn.commit()
                
                cursor.close()
                conn.close()
                
                # Redirect to appropriate dashboard
                dashboard_route = get_dashboard_route(user['user_type'])
                print(f"\n✅ Login successful: {username} ({user['user_type']})")
                print(f"   Redirecting to: {dashboard_route}\n")
                return redirect(dashboard_route)
            else:
                cursor.close()
                conn.close()
                return render_template_string(LOGIN_TEMPLATE, error="Invalid username or inactive account.")
                
        except Exception as e:
            cursor.close()
            conn.close()
            print(f"Database error: {e}")
            return render_template_string(LOGIN_TEMPLATE, error="Database connection error")
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/')
def index():
    return redirect('/login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/unauthorized')
def unauthorized():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unauthorized</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .container { background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; }
            h1 { color: #e74c3c; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚫 Unauthorized Access</h1>
            <p>You don't have permission to view this page.</p>
            <a href="/login">Back to Login</a>
        </div>
    </body>
    </html>
    '''

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/login')
    return f'<h1>Welcome {session.get("username")}</h1><p>User Type: {session.get("user_type")}</p><a href="/logout">Logout</a>'

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏫 SCHOOL MANAGEMENT SYSTEM - WORKING")
    print("="*60)
    print(f"Server: http://127.0.0.1:5000")
    print(f"Login: http://127.0.0.1:5000/login")
    print("\n" + "="*60)
    print("REGISTERED ROUTES:")
    print("="*60)
    for rule in app.url_map.iter_rules():
        if 'director' in str(rule) or 'dashboard' in str(rule):
            print(f"  {rule}")
    print("\n" + "="*60)
    print("🔑 TEST LOGIN (any password):")
    print("="*60)
    print("  Director: director001")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)