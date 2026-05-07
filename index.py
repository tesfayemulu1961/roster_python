from flask import Flask, render_template_string, session, redirect, request
from datetime import datetime
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

# Landing Page Template
LANDING_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>School Management System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        
        header {
            background-color: #2c3e50;
            color: white;
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
        }
        
        .logo-container {
            display: flex;
            align-items: center;
        }
        
        .logo {
            height: 60px;
            width: 60px;
            margin-right: 15px;
            background-color: #3498db;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
        }
        
        .school-name h1 {
            font-size: 1.5rem;
            margin-bottom: 5px;
        }
        
        .school-name p {
            font-size: 0.8rem;
            opacity: 0.8;
        }
        
        .cta-button {
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 10px 25px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            transition: background-color 0.3s;
        }
        
        .cta-button:hover {
            background-color: #2980b9;
        }
        
        main {
            flex: 1;
            padding: 100px 2rem 60px;
            max-width: 1200px;
            margin: 0 auto;
            width: 100%;
        }
        
        .hero {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        .hero h2 {
            font-size: 2.2rem;
            color: #2c3e50;
            margin-bottom: 1rem;
        }
        
        .hero p {
            font-size: 1rem;
            color: #555;
            max-width: 800px;
            margin: 0 auto 1.5rem;
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }
        
        .feature-card {
            background-color: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
        }
        
        .feature-card h3 {
            color: #2c3e50;
            margin-bottom: 0.8rem;
            font-size: 1.2rem;
        }
        
        .feature-card p {
            color: #666;
            font-size: 0.9rem;
        }
        
        footer {
            background-color: #2c3e50;
            color: white;
            text-align: center;
            padding: 1.5rem;
            margin-top: auto;
        }
        
        .developers {
            font-size: 0.85rem;
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            header {
                flex-direction: column;
                text-align: center;
                padding: 1rem;
            }
            
            .logo-container {
                margin-bottom: 0.5rem;
                justify-content: center;
            }
            
            main {
                padding: 140px 1rem 60px;
            }
            
            .hero h2 {
                font-size: 1.5rem;
            }
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
</head>
<body>
    <header>
        <div class="logo-container">
            <div class="logo">
                <i class="fas fa-graduation-cap"></i>
            </div>
            <div class="school-name">
                <h1>Ethio School Management System</h1>
                <p>Excellence in Education</p>
            </div>
        </div>
        <div class="auth-buttons">
            <a href="/login" class="cta-button">Login</a>
        </div>
    </header>
    
    <main>
        <section class="hero">
            <h2>Comprehensive School Management Solution</h2>
            <p>Streamlining student exam result recording and data analysis for KG, First and Medium Schools in Ethiopia.</p>
            <a href="#" class="cta-button">Learn More</a>
        </section>
        
        <section class="features">
            <div class="feature-card">
                <h3>Student Result Management</h3>
                <p>Efficiently record, analyze, and report student exam results with automated calculations for sum, average, and ranking.</p>
            </div>
            
            <div class="feature-card">
                <h3>Academic Year Structure</h3>
                <p>Supports Ethiopian academic calendar with two semesters and multiple grade levels.</p>
            </div>
            
            <div class="feature-card">
                <h3>Comprehensive Data Analysis</h3>
                <p>Generate subject-wise and grade-level analysis reports to identify trends and improve educational outcomes.</p>
            </div>
            
            <div class="feature-card">
                <h3>Multi-User Access</h3>
                <p>Role-based access for registrars, teachers, supervisors, and administrators with appropriate permissions.</p>
            </div>
            
            <div class="feature-card">
                <h3>Parent & Student Portal</h3>
                <p>Secure access for parents and students to view results using roll number or school ID.</p>
            </div>
            
            <div class="feature-card">
                <h3>Document Management</h3>
                <p>Upload, download, and manage textbooks, teacher guides, and important school documents.</p>
            </div>
        </section>
    </main>
    
    <footer>
        <div class="developers">
            <p>Developed by: Tesfaye Mulu</p>
            <p>&copy; 2025 Ethio School Management System. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>
'''

# Login Template
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - School Management System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        body {
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
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        .login-header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        .login-header p {
            color: #666;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
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
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
        .back-link {
            text-align: center;
            margin-top: 20px;
        }
        .back-link a {
            color: #667eea;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>🔐 School Management System</h1>
            <p>Enter your credentials to access the system</p>
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

# Director Dashboard (Simple)
DIRECTOR_DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <title>Director Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f4f4f4; }
        .header { background: #2c3e50; color: white; padding: 15px; margin-bottom: 20px; }
        .logout-btn { background: #e74c3c; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Director Dashboard</h1>
        <a href="/logout" class="logout-btn">Logout</a>
    </div>
    <div class="container">
        <p>Welcome, {{ username }}!</p>
        <p>User Type: Director</p>
    </div>
</body>
</html>
'''

# Teacher Dashboard
TEACHER_DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <title>Teacher Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f4f4f4; }
        .header { background: #3498db; color: white; padding: 15px; margin-bottom: 20px; }
        .logout-btn { background: #e74c3c; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Teacher Dashboard</h1>
        <a href="/logout" class="logout-btn">Logout</a>
    </div>
    <div class="container">
        <p>Welcome, {{ username }}!</p>
        <p>User Type: {{ user_type }}</p>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """Landing page"""
    return LANDING_PAGE

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, username, user_type FROM users WHERE username = %s AND account_status = 'active'", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            
            if user['user_type'] == 'director':
                return redirect('/director/dashboard')
            elif 'room teacher' in user['user_type'].lower():
                return redirect('/teacher/dashboard')
            else:
                return redirect('/dashboard')
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Invalid username")
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/director/dashboard')
def director_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    if session.get('user_type') != 'director':
        return "Access Denied", 403
    return render_template_string(DIRECTOR_DASHBOARD, username=session.get('username'))

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template_string(TEACHER_DASHBOARD, 
                                  username=session.get('username'),
                                  user_type=session.get('user_type'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return f"<h1>Dashboard</h1><p>Welcome {session.get('username')}</p><p>User Type: {session.get('user_type')}</p><a href='/logout'>Logout</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    print("\n" + "="*50)
    print("ETHIO SCHOOL MANAGEMENT SYSTEM")
    print("="*50)
    print("Server: http://127.0.0.1:5000")
    print("Home Page: http://127.0.0.1:5000/")
    print("Login: http://127.0.0.1:5000/login")
    print("Director Dashboard: http://127.0.0.1:5000/director/dashboard")
    print("Teacher Dashboard: http://127.0.0.1:5000/teacher/dashboard")
    print("\nTest Login:")
    print("  Director: director001 (any password)")
    print("  Teacher: TCH-001 (any password)")
    print("="*50 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)