from flask import Flask, render_template_string, session, redirect, request
from datetime import datetime, timedelta
import mysql.connector

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
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
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
        h2 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
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
        button:hover {
            opacity: 0.9;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
        .success {
            background: #d4edda;
            color: #155724;
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
        {% if success %}
        <div class="success">{{ success }}</div>
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
    </div>
</body>
</html>
'''

# ============== DIRECTOR DASHBOARD ==============
@app.route('/director/dashboard')
def director_dashboard():
    if not session.get('logged_in'):
        return redirect('/login')
    if session.get('user_type') != 'director':
        return redirect('/unauthorized')
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Director Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .container { padding: 20px; max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .stat-card { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .stat-number { font-size: 32px; font-weight: bold; color: #667eea; }
            button { background: #e74c3c; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            .btn { background: #667eea; margin-right: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 Director Dashboard</h1>
            <div>
                <span>Welcome, {{ session.get('username') }}!</span>
                <button onclick="location.href='/logout'">Logout</button>
            </div>
        </div>
        <div class="container">
            <div class="card">
                <h2>Welcome to the Director Dashboard</h2>
                <p>Role: School Director</p>
                <p>User Type: {{ session.get('user_type') }}</p>
            </div>
            
            <div class="stats">
                <div class="stat-card"><h3>Total Students</h3><div class="stat-number">1,234</div></div>
                <div class="stat-card"><h3>Total Teachers</h3><div class="stat-number">45</div></div>
                <div class="stat-card"><h3>Total Classes</h3><div class="stat-number">32</div></div>
                <div class="stat-card"><h3>Active Sections</h3><div class="stat-number">28</div></div>
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

# ============== ROOM TEACHER DASHBOARD - GRADE 6A ==============
@app.route('/room_teacher/grade_6A/dashboard')
def room_teacher_grade_6A_dashboard():
    if not session.get('logged_in'):
        return redirect('/login')
    if session.get('user_type') != 'room teacher grade 6th A':
        return redirect('/unauthorized')
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Grade 6A Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .container { padding: 20px; max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .feature-card { background: white; padding: 20px; border-radius: 8px; text-align: center; cursor: pointer; transition: transform 0.3s; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .feature-card:hover { transform: translateY(-5px); }
            button { background: #e74c3c; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📚 Grade 6A - Room Teacher Dashboard</h1>
            <button onclick="location.href='/logout'">Logout</button>
        </div>
        <div class="container">
            <div class="card">
                <h2>Welcome, Teacher!</h2>
                <p>Class: Grade 6 - Section A</p>
                <p>Total Students: 35</p>
                <p>Academic Year: 2024-2025</p>
            </div>
            
            <div class="grid">
                <div class="feature-card" onclick="alert('Take Attendance - Coming Soon')">
                    <h3>📋 Take Attendance</h3>
                    <p>Mark student attendance for today</p>
                </div>
                <div class="feature-card" onclick="alert('Record Grades - Coming Soon')">
                    <h3>📊 Record Grades</h3>
                    <p>Enter student assessment scores</p>
                </div>
                <div class="feature-card" onclick="alert('View Students - Coming Soon')">
                    <h3>👨‍🎓 View Students</h3>
                    <p>Manage student information</p>
                </div>
                <div class="feature-card" onclick="alert('Generate Reports - Coming Soon')">
                    <h3>📈 Generate Reports</h3>
                    <p>Create class performance reports</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

# ============== ROOM TEACHER DASHBOARD - GRADE 6B ==============
@app.route('/room_teacher/grade_6B/dashboard')
def room_teacher_grade_6B_dashboard():
    if not session.get('logged_in'):
        return redirect('/login')
    if session.get('user_type') != 'room teacher grade 6th B':
        return redirect('/unauthorized')
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Grade 6B Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .container { padding: 20px; max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .feature-card { background: white; padding: 20px; border-radius: 8px; text-align: center; cursor: pointer; transition: transform 0.3s; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            button { background: #e74c3c; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📚 Grade 6B - Room Teacher Dashboard</h1>
            <button onclick="location.href='/logout'">Logout</button>
        </div>
        <div class="container">
            <div class="card">
                <h2>Welcome, Teacher!</h2>
                <p>Class: Grade 6 - Section B</p>
                <p>Total Students: 32</p>
                <p>Academic Year: 2024-2025</p>
            </div>
            <div class="grid">
                <div class="feature-card" onclick="alert('Take Attendance - Coming Soon')"><h3>📋 Take Attendance</h3></div>
                <div class="feature-card" onclick="alert('Record Grades - Coming Soon')"><h3>📊 Record Grades</h3></div>
                <div class="feature-card" onclick="alert('View Students - Coming Soon')"><h3>👨‍🎓 View Students</h3></div>
                <div class="feature-card" onclick="alert('Generate Reports - Coming Soon')"><h3>📈 Generate Reports</h3></div>
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
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }}
            .container {{ padding: 40px; max-width: 600px; margin: 0 auto; }}
            .card {{ background: white; padding: 30px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            button {{ background: #e74c3c; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-top: 20px; }}
            .info {{ background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Welcome {session.get('username')}!</h1>
            <button onclick="location.href='/logout'">Logout</button>
        </div>
        <div class="container">
            <div class="card">
                <h2>📱 {session.get('user_type')} Dashboard</h2>
                <div class="info">
                    <p><strong>Username:</strong> {session.get('username')}</p>
                    <p><strong>User Type:</strong> {session.get('user_type')}</p>
                    <p><strong>Status:</strong> Logged In</p>
                </div>
                <p>This dashboard is currently under development.</p>
            </div>
        </div>
    </body>
    </html>
    '''

# ============== UNAUTHORIZED PAGE ==============
@app.route('/unauthorized')
def unauthorized():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unauthorized</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .container { background: white; padding: 30px; border-radius: 8px; max-width: 500px; margin: 0 auto; }
            h1 { color: #e74c3c; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Unauthorized Access</h1>
            <p>You don't have permission to view this page.</p>
            <a href="/login">Back to Login</a>
        </div>
    </body>
    </html>
    '''

# ============== DASHBOARD ROUTE MAPPING ==============
def get_dashboard_route(user_type):
    """Return the appropriate dashboard route based on user type"""
    
    # Directors
    if user_type == 'director':
        return '/director/dashboard'
    elif user_type == 'vice director':
        return '/vice_director/dashboard'
    elif user_type == 'supervisor':
        return '/supervisor/dashboard'
    elif user_type == 'KG director':
        return '/kg_director/dashboard'
    
    # Room Teachers - Grade 8
    elif user_type == 'room teacher grade 8th A':
        return '/room_teacher/grade_8A/dashboard'
    elif user_type == 'room teacher grade 8th B':
        return '/room_teacher/grade_8B/dashboard'
    elif user_type == 'room teacher grade 8th C':
        return '/room_teacher/grade_8C/dashboard'
    elif user_type == 'room teacher grade 8th D':
        return '/room_teacher/grade_8D/dashboard'
    
    # Room Teachers - Grade 7
    elif user_type == 'room teacher grade 7th A':
        return '/room_teacher/grade_7A/dashboard'
    elif user_type == 'room teacher grade 7th B':
        return '/room_teacher/grade_7B/dashboard'
    elif user_type == 'room teacher grade 7th C':
        return '/room_teacher/grade_7C/dashboard'
    elif user_type == 'room teacher grade 7th D':
        return '/room_teacher/grade_7D/dashboard'
    
    # Room Teachers - Grade 6
    elif user_type == 'room teacher grade 6th A':
        return '/room_teacher/grade_6A/dashboard'
    elif user_type == 'room teacher grade 6th B':
        return '/room_teacher/grade_6B/dashboard'
    elif user_type == 'room teacher grade 6th C':
        return '/room_teacher/grade_6C/dashboard'
    elif user_type == 'room teacher grade 6th D':
        return '/room_teacher/grade_6D/dashboard'
    
    # Room Teachers - Grade 5
    elif user_type == 'room teacher grade 5th A':
        return '/room_teacher/grade_5A/dashboard'
    elif user_type == 'room teacher grade 5th B':
        return '/room_teacher/grade_5B/dashboard'
    elif user_type == 'room teacher grade 5th C':
        return '/room_teacher/grade_5C/dashboard'
    elif user_type == 'room teacher grade 5th D':
        return '/room_teacher/grade_5D/dashboard'
    
    # Room Teachers - Grade 4
    elif user_type == 'room teacher grade 4th A':
        return '/room_teacher/grade_4A/dashboard'
    elif user_type == 'room teacher grade 4th B':
        return '/room_teacher/grade_4B/dashboard'
    elif user_type == 'room teacher grade 4th C':
        return '/room_teacher/grade_4C/dashboard'
    elif user_type == 'room teacher grade 4th D':
        return '/room_teacher/grade_4D/dashboard'
    
    # Room Teachers - Grade 3
    elif user_type == 'room teacher grade 3rd A':
        return '/room_teacher/grade_3A/dashboard'
    elif user_type == 'room teacher grade 3rd B':
        return '/room_teacher/grade_3B/dashboard'
    elif user_type == 'room teacher grade 3rd C':
        return '/room_teacher/grade_3C/dashboard'
    elif user_type == 'room teacher grade 3rd D':
        return '/room_teacher/grade_3D/dashboard'
    
    # Room Teachers - Grade 2
    elif user_type == 'room teacher grade 2nd A':
        return '/room_teacher/grade_2A/dashboard'
    elif user_type == 'room teacher grade 2nd B':
        return '/room_teacher/grade_2B/dashboard'
    elif user_type == 'room teacher grade 2nd C':
        return '/room_teacher/grade_2C/dashboard'
    elif user_type == 'room teacher grade 2nd D':
        return '/room_teacher/grade_2D/dashboard'
    
    # Room Teachers - Grade 1
    elif user_type == 'room teacher grade 1st A':
        return '/room_teacher/grade_1A/dashboard'
    elif user_type == 'room teacher grade 1st B':
        return '/room_teacher/grade_1B/dashboard'
    elif user_type == 'room teacher grade 1st C':
        return '/room_teacher/grade_1C/dashboard'
    elif user_type == 'room teacher grade 1st D':
        return '/room_teacher/grade_1D/dashboard'
    elif user_type == 'room teacher grade 1st E':
        return '/room_teacher/grade_1E/dashboard'
    
    # Students & Parents
    elif 'student' in user_type.lower():
        return '/student/dashboard'
    elif user_type == 'parent' or user_type == '':
        return '/parent/dashboard'
    
    # Default fallback
    else:
        return '/dashboard'
        
# ============== DYNAMIC DASHBOARD ROUTE MAPPING ==============
def get_dashboard_route_dynamic(user_type):
    """Dynamically get dashboard route for any room teacher"""
    
    # Check if it's a room teacher
    if 'room teacher grade' in user_type.lower():
        import re
        # Extract grade and section (e.g., "room teacher grade 6th A" -> "6A")
        match = re.search(r'grade (\d+)(?:st|nd|rd|th)?\s*([A-E])', user_type, re.IGNORECASE)
        if match:
            grade = match.group(1)
            section = match.group(2)
            return f'/room_teacher/grade_{grade}{section}/dashboard'
    
    # Directors
    if user_type == 'director':
        return '/director/dashboard'
    elif user_type == 'vice director':
        return '/vice_director/dashboard'
    elif user_type == 'supervisor':
        return '/supervisor/dashboard'
    elif user_type == 'KG director':
        return '/kg_director/dashboard'
    
    # Students and Parents
    elif 'student' in user_type.lower():
        return '/student/dashboard'
    elif user_type == 'parent' or user_type == '':
        return '/parent/dashboard'
    
    # Default
    return '/dashboard'
    
# Dynamic dashboard route for room teachers
@app.route('/room_teacher/<grade_section>/dashboard')
def room_teacher_dashboard(grade_section):
    if not session.get('logged_in'):
        return redirect('/login')
    
    user_type = session.get('user_type')
    expected_type = f"room teacher grade {grade_section.lower().replace('_', 'th ')}".replace('th grade', 'grade')
    
    # For grade_6A -> "room teacher grade 6th A"
    expected = f"room teacher grade {grade_section[0]}th {grade_section[1]}"
    
    if user_type != expected:
        return redirect('/unauthorized')
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Grade {grade_section} Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; }}
            .container {{ padding: 20px; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            button {{ background: #e74c3c; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }}
            .feature {{ background: white; padding: 20px; border-radius: 8px; text-align: center; cursor: pointer; }}
            .feature:hover {{ transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Grade {grade_section} - Room Teacher Dashboard</h1>
            <p>Welcome, {session.get('username')}!</p>
            <button onclick="location.href='/logout'">Logout</button>
        </div>
        <div class="container">
            <div class="card">
                <h2>Class Management</h2>
                <p>User Type: {session.get('user_type')}</p>
            </div>
            <div class="grid">
                <div class="feature" onclick="alert('Attendance - Coming Soon')">
                    <h3>📋 Take Attendance</h3>
                </div>
                <div class="feature" onclick="alert('Grades - Coming Soon')">
                    <h3>📊 Record Grades</h3>
                </div>
                <div class="feature" onclick="alert('Students - Coming Soon')">
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
            cursor.execute("SELECT user_id, username, user_type, reference_id, account_status FROM users WHERE username = %s LIMIT 1", (username,))
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
                dashboard_route = get_dashboard_route_dynamic(user['user_type'])
                return redirect(dashboard_route)
            else:
                cursor.close()
                conn.close()
                return render_template_string(LOGIN_TEMPLATE, error="Invalid username or password.")
        except Exception as e:
            cursor.close()
            conn.close()
            print(f"Database error: {e}")
            return render_template_string(LOGIN_TEMPLATE, error="Database connection error. Please try again.")
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/')
def index():
    return redirect('/login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
    
    # ============== ADDITIONAL DASHBOARDS ==============

# Vice Director Dashboard
@app.route('/vice_director/dashboard')
def vice_director_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'vice director':
        return redirect('/unauthorized')
    return f'<h1>Vice Director Dashboard</h1><p>Welcome {session.get("username")}</p><a href="/logout">Logout</a>'

# Supervisor Dashboard
@app.route('/supervisor/dashboard')
def supervisor_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'supervisor':
        return redirect('/unauthorized')
    return f'<h1>Supervisor Dashboard</h1><p>Welcome {session.get("username")}</p><a href="/logout">Logout</a>'

# KG Director Dashboard
@app.route('/kg_director/dashboard')
def kg_director_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'KG director':
        return redirect('/unauthorized')
    return f'<h1>KG Director Dashboard</h1><p>Welcome {session.get("username")}</p><a href="/logout">Logout</a>'

# Student Dashboard
@app.route('/student/dashboard')
def student_dashboard():
    if not session.get('logged_in') or 'student' not in session.get('user_type', '').lower():
        return redirect('/unauthorized')
    return f'<h1>Student Dashboard</h1><p>Welcome {session.get("username")}</p><a href="/logout">Logout</a>'

# Parent Dashboard
@app.route('/parent/dashboard')
def parent_dashboard():
    if not session.get('logged_in'):
        return redirect('/unauthorized')
    return f'<h1>Parent Dashboard</h1><p>Welcome {session.get("username")}</p><a href="/logout">Logout</a>'
    

if __name__ == '__main__':
    print("\n" + "="*60)
    print("SCHOOL MANAGEMENT SYSTEM - LOGIN PORTAL")
    print("="*60)
    print(f"Server: http://127.0.0.1:5000")
    print(f"Login: http://127.0.0.1:5000/login")
    print("\n" + "="*60)
    print("TEST LOGINS (use any password):")
    print("="*60)
    print("  Director:           director001")
    print("  Grade 6A Teacher:   TCH-002 (room teacher grade 6th A)")
    print("  Grade 6B Teacher:   TCH-003 (room teacher grade 6th B)")
    print("\n" + "="*60)
    
    app.run(debug=True, host='127.0.0.1', port=5000)