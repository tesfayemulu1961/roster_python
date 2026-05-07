from flask import Flask, render_template_string, session, redirect, request
from datetime import datetime
import mysql.connector
import re

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

# ============== DIRECTOR DASHBOARD (SIMPLE VERSION) ==============
@app.route('/director/director_dashboard')
def director_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return redirect('/unauthorized')
    
    # Try to use the converted dashboard, but if it fails, use fallback
    try:
        from director.director_dashboard import director_dashboard_bp
        # If we have the blueprint, we can redirect to its route
        # But since it's registered, we can just let it work
        # For now, use a simple dashboard
        return simple_director_dashboard()
    except:
        return simple_director_dashboard()

def simple_director_dashboard():
    """Simple fallback director dashboard"""
    username = session.get('username', 'User')
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Director Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }}
            .container {{ padding: 20px; max-width: 1200px; margin: 0 auto; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
            .stat-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; }}
            .stat-number {{ font-size: 32px; font-weight: bold; color: #667eea; }}
            button {{ background: #e74c3c; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
            .btn {{ background: #667eea; margin-right: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 Director Dashboard</h1>
            <div>
                <span>Welcome, {username}!</span>
                <button onclick="location.href='/logout'">Logout</button>
            </div>
        </div>
        <div class="container">
            <div class="card">
                <h2>School Director Dashboard</h2>
                <p>Role: School Director</p>
                <p>User Type: {session.get('user_type')}</p>
                <p>This is the Python version of the Director Dashboard</p>
            </div>
            <div class="stats">
                <div class="stat-card"><h3>Total Students</h3><div class="stat-number">1,234</div></div>
                <div class="stat-card"><h3>Total Teachers</h3><div class="stat-number">45</div></div>
                <div class="stat-card"><h3>Total Classes</h3><div class="stat-number">32</div></div>
            </div>
            <div class="card">
                <h3>Quick Actions</h3>
                <button class="btn" onclick="alert('Manage Students - Coming Soon')">Manage Students</button>
                <button class="btn" onclick="alert('Manage Teachers - Coming Soon')">Manage Teachers</button>
                <button class="btn" onclick="alert('View Reports - Coming Soon')">View Reports</button>
            </div>
        </div>
    </body>
    </html>
    '''

# ============== ROOM TEACHER DASHBOARD (SIMPLE VERSION) ==============
@app.route('/room_teacher/grade_6A/grade_6A_rt_dashboard')
def grade_6A_teacher_dashboard():
    if not session.get('logged_in'):
        return redirect('/login')
    
    username = session.get('username', 'Teacher')
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Grade 6A Teacher Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }}
            .container {{ padding: 20px; max-width: 1200px; margin: 0 auto; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
            .feature {{ background: white; padding: 20px; border-radius: 8px; text-align: center; cursor: pointer; }}
            button {{ background: #e74c3c; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📚 Grade 6A - Room Teacher Dashboard</h1>
            <button onclick="location.href='/logout'">Logout</button>
        </div>
        <div class="container">
            <div class="card">
                <h2>Welcome, Teacher {username}!</h2>
                <p>Class: Grade 6 - Section A</p>
                <p>User Type: {session.get('user_type')}</p>
            </div>
            <div class="grid">
                <div class="feature" onclick="alert('Take Attendance - Coming Soon')">
                    <h3>📋 Take Attendance</h3>
                </div>
                <div class="feature" onclick="alert('Record Grades - Coming Soon')">
                    <h3>📊 Record Grades</h3>
                </div>
                <div class="feature" onclick="alert('View Students - Coming Soon')">
                    <h3>👨‍🎓 View Students</h3>
                </div>
                <div class="feature" onclick="alert('Reports - Coming Soon')">
                    <h3>📈 Generate Reports</h3>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

# ============== GENERIC DASHBOARD ==============
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/login')
    return f'''
    <h1>Welcome {session.get("username")}</h1>
    <p>User Type: {session.get("user_type")}</p>
    <a href="/logout">Logout</a>
    '''

# ============== DASHBOARD ROUTE MAPPING ==============
def get_dashboard_route(user_type):
    """Return the appropriate dashboard route based on user type"""
    
    if user_type == 'director':
        return '/director/director_dashboard'
    elif 'room teacher grade 6th A' in user_type:
        return '/room_teacher/grade_6A/grade_6A_rt_dashboard'
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
    return '<h1>Unauthorized Access</h1><p>You don\'t have permission.</p><a href="/login">Login</a>'

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏫 SCHOOL MANAGEMENT SYSTEM - WORKING VERSION")
    print("="*60)
    print(f"Server: http://127.0.0.1:5000")
    print(f"Login: http://127.0.0.1:5000/login")
    print("\n" + "="*60)
    print("TEST LOGINS (any password):")
    print("="*60)
    print("  Director:           director001")
    print("  Grade 6A Teacher:   TCH-002")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)