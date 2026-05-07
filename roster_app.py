from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from flask_cors import CORS
import mysql.connector
from functools import wraps
import hashlib
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'
CORS(app)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db():
    return mysql.connector.connect(**db_config)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Role required decorator
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('user_type') != role:
                return "Access denied. You don't have permission to view this page.", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# HTML Templates
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roster Management System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            width: 90%;
            max-width: 1200px;
            padding: 40px;
        }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { color: #333; margin-bottom: 10px; }
        .header p { color: #666; }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .feature-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            transition: transform 0.3s;
        }
        .feature-card:hover { transform: translateY(-5px); }
        .feature-card h3 { color: #667eea; margin-bottom: 10px; }
        .feature-card p { color: #666; font-size: 14px; }
        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 20px;
        }
        .btn-login { display: block; text-align: center; max-width: 200px; margin: 0 auto; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏫 Roster Management System</h1>
            <p>School Management System - Director Dashboard</p>
        </div>
        <div class="features">
            <div class="feature-card">
                <h3>👥 User Management</h3>
                <p>Manage directors, supervisors, teachers, and students</p>
            </div>
            <div class="feature-card">
                <h3>📊 Student Scores</h3>
                <p>Track and manage student academic performance</p>
            </div>
            <div class="feature-card">
                <h3>📈 Reports</h3>
                <p>Generate comprehensive reports and analytics</p>
            </div>
            <div class="feature-card">
                <h3>👩‍🏫 Teacher Management</h3>
                <p>Manage teacher assignments and subjects</p>
            </div>
        </div>
        <a href="/login" class="btn btn-login">🔐 Login to Dashboard</a>
    </div>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Roster System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            width: 400px;
            padding: 40px;
        }
        .login-header { text-align: center; margin-bottom: 30px; }
        .login-header h1 { color: #333; margin-bottom: 10px; }
        .login-header p { color: #666; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: 500; }
        input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        input:focus { outline: none; border-color: #667eea; }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover { transform: translateY(-2px); }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
            text-align: center;
        }
        .back-link {
            text-align: center;
            margin-top: 20px;
        }
        .back-link a { color: #667eea; text-decoration: none; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>🔐 Login</h1>
            <p>Enter your credentials to access the dashboard</p>
        </div>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Login</button>
        </form>
        <div class="back-link">
            <a href="/">← Back to Home</a>
        </div>
    </div>
</body>
</html>
'''

DIRECTOR_DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Director Dashboard - Roster System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f4f4; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 24px; }
        .user-info { display: flex; align-items: center; gap: 15px; }
        .logout-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 5px;
            cursor: pointer;
        }
        .container { max-width: 1400px; margin: 30px auto; padding: 0 20px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-card .number { font-size: 36px; font-weight: bold; color: #667eea; }
        .stat-card label { color: #666; margin-top: 10px; display: block; }
        .section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .section h2 { margin-bottom: 20px; color: #333; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; color: #333; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #ddd; }
        .tab {
            padding: 10px 20px;
            background: none;
            border: none;
            cursor: pointer;
            color: #666;
        }
        .tab.active { color: #667eea; border-bottom: 2px solid #667eea; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏫 Director Dashboard - Roster Management System</h1>
        <div class="user-info">
            <span>Welcome, {{ username }} ({{ user_type }})</span>
            <button class="logout-btn" onclick="window.location.href='/logout'">Logout</button>
        </div>
    </div>
    <div class="container">
        <div class="stats">
            <div class="stat-card"><div class="number">{{ total_users }}</div><label>Total Users</label></div>
            <div class="stat-card"><div class="number">{{ total_students }}</div><label>Total Students</label></div>
            <div class="stat-card"><div class="number">{{ total_teachers }}</div><label>Total Teachers</label></div>
            <div class="stat-card"><div class="number">{{ total_parents }}</div><label>Total Parents</label></div>
        </div>
        
        <div class="section">
            <div class="tabs">
                <button class="tab active" onclick="showTab('users')">Users</button>
                <button class="tab" onclick="showTab('students')">Students</button>
                <button class="tab" onclick="showTab('teachers')">Teachers</button>
                <button class="tab" onclick="showTab('parents')">Parents</button>
            </div>
            
            <div id="usersTab" class="tab-content active">
                <table>
                    <thead><tr><th>ID</th><th>Username</th><th>User Type</th><th>Status</th></tr></thead>
                    <tbody>
                        {% for user in users %}
                        <tr><td>{{ user.user_id }}</td><td>{{ user.username }}</td><td>{{ user.user_type }}</td><td>{{ user.account_status }}</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div id="studentsTab" class="tab-content">
                <table>
                    <thead><tr><th>Student ID</th><th>Name</th><th>Grade</th><th>Section</th></tr></thead>
                    <tbody>
                        {% for student in students %}
                        <tr><td>{{ student.studid }}</td><td>{{ student.fullname }}</td><td>{{ student.grade }}</td><td>{{ student.section }}</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div id="teachersTab" class="tab-content">
                <table>
                    <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th></tr></thead>
                    <tbody>
                        {% for teacher in teachers %}
                        <tr><td>{{ teacher.id }}</td><td>{{ teacher.name }}</td><td>{{ teacher.email }}</td><td>{{ teacher.phone }}</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div id="parentsTab" class="tab-content">
                <table>
                    <thead><tr><th>ID</th><th>Name</th><th>Phone</th><th>Email</th></tr></thead>
                    <tbody>
                        {% for parent in parents %}
                        <tr><td>{{ parent.id }}</td><td>{{ parent.name }}</td><td>{{ parent.phone }}</td><td>{{ parent.email }}</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(tabName + 'Tab').classList.add('active');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT user_id, username, user_type, account_status FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user and user['account_status'] == 'active':
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            
            if user['user_type'] == 'director':
                return redirect(url_for('director_dashboard'))
            elif 'teacher' in user['user_type']:
                return redirect(url_for('teacher_dashboard'))
            else:
                return render_template_string(LOGIN_TEMPLATE, error="Access denied. Only directors can access this dashboard.")
        
        return render_template_string(LOGIN_TEMPLATE, error="Invalid username or account inactive")
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/director-dashboard')
@login_required
def director_dashboard():
    if session.get('user_type') != 'director':
        return "Access denied", 403
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get counts
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM student")
    total_students = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM teacher")
    total_teachers = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM parent")
    total_parents = cursor.fetchone()['count']
    
    # Get lists
    cursor.execute("SELECT user_id, username, user_type, account_status FROM users LIMIT 50")
    users = cursor.fetchall()
    
    cursor.execute("SELECT studid, fullname, grade, section FROM student LIMIT 50")
    students = cursor.fetchall()
    
    cursor.execute("SELECT id, name, email, phone FROM teacher LIMIT 50")
    teachers = cursor.fetchall()
    
    cursor.execute("SELECT id, name, phone, email FROM parent LIMIT 50")
    parents = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template_string(DIRECTOR_DASHBOARD_TEMPLATE,
                                  username=session['username'],
                                  user_type=session['user_type'],
                                  total_users=total_users,
                                  total_students=total_students,
                                  total_teachers=total_teachers,
                                  total_parents=total_parents,
                                  users=users,
                                  students=students,
                                  teachers=teachers,
                                  parents=parents)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("\n" + "="*50)
    print("ROSTER MANAGEMENT SYSTEM - PYTHON VERSION")
    print("="*50)
    print("Server: http://127.0.0.1:5000")
    print("\nAccess:")
    print("  http://127.0.0.1:5000/ - Home Page")
    print("  http://127.0.0.1:5000/login - Login Page")
    print("  http://127.0.0.1:5000/director-dashboard - Director Dashboard")
    print("\nTest Login (any password works):")
    print("  Username: director001")
    print("  Username: director")
    print("="*50 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)