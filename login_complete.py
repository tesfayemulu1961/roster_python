from flask import Flask, render_template_string, session, redirect, request
from datetime import datetime
import mysql.connector
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db():
    return mysql.connector.connect(**db_config)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>School Management System - Login</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;justify-content:center;align-items:center}
        .login-container{background:white;padding:40px;border-radius:10px;box-shadow:0 15px 35px rgba(0,0,0,0.2);width:400px}
        h2{text-align:center;color:#333;margin-bottom:30px}
        .form-group{margin-bottom:20px}
        label{display:block;margin-bottom:8px;color:#555;font-weight:500}
        input{width:100%;padding:12px;border:2px solid #e0e0e0;border-radius:6px;font-size:14px}
        input:focus{outline:none;border-color:#667eea}
        button{width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:6px;font-size:16px;font-weight:bold;cursor:pointer}
        button:hover{transform:translateY(-2px)}
        .error{background:#fee;color:#c33;padding:12px;border-radius:6px;margin-bottom:20px;text-align:center;border-left:4px solid #c33}
        .info{text-align:center;margin-top:20px;color:#666;font-size:12px}
    </style>
</head>
<body>
    <div class="login-container">
        <h2>School Management System</h2>
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
        <div class="info">
            Enter your username and password
        </div>
    </div>
</body>
</html>
'''

def get_dashboard_url(user_type, username):
    """Map database user_type to actual PHP dashboard URL"""
    
    print(f"DEBUG: Mapping user_type: '{user_type}'")
    
    # Directors
    if user_type == 'director':
        return 'http://localhost/roster_php/director/director_dashboard.php'
    
    if user_type == 'vice director':
        return 'http://localhost/roster_php/vice_director/vice_director_dashboard.php'
    
    if user_type == 'supervisor':
        return 'http://localhost/roster_php/supervisor/supervisor_dashboard.php'
    
    if user_type == 'KG director':
        return 'http://localhost/roster_php/kg_director/kg_director_dashboard.php'
    
    # Room Teachers - Grade 1
    if 'room teacher grade 1st' in user_type.lower():
        if 'A' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_1A/grade_1A_rt_dashboard.php'
        elif 'B' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_1B/grade_1B_rt_dashboard.php'
        elif 'C' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_1C/grade_1C_rt_dashboard.php'
        elif 'D' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_1D/grade_1D_rt_dashboard.php'
        elif 'E' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_1E/grade_1E_rt_dashboard.php'
    
    # Room Teachers - Grade 2
    if 'room teacher grade 2nd' in user_type.lower():
        if 'A' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_2A/grade_2A_rt_dashboard.php'
        elif 'B' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_2B/grade_2B_rt_dashboard.php'
        elif 'C' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_2C/grade_2C_rt_dashboard.php'
        elif 'D' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_2D/grade_2D_rt_dashboard.php'
    
    # Room Teachers - Grade 3
    if 'room teacher grade 3rd' in user_type.lower():
        if 'A' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_3A/grade_3A_rt_dashboard.php'
        elif 'B' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_3B/grade_3B_rt_dashboard.php'
        elif 'C' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_3C/grade_3C_rt_dashboard.php'
        elif 'D' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_3D/grade_3D_rt_dashboard.php'
    
    # Room Teachers - Grade 4
    if 'room teacher grade 4th' in user_type.lower():
        if 'A' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_4A/grade_4A_rt_dashboard.php'
        elif 'B' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_4B/grade_4B_rt_dashboard.php'
        elif 'C' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_4C/grade_4C_rt_dashboard.php'
        elif 'D' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_4D/grade_4D_rt_dashboard.php'
    
    # Room Teachers - Grade 5
    if 'room teacher grade 5th' in user_type.lower():
        if 'A' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_5A/grade_5A_rt_dashboard.php'
        elif 'B' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_5B/grade_5B_rt_dashboard.php'
        elif 'C' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_5C/grade_5C_rt_dashboard.php'
        elif 'D' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_5D/grade_5D_rt_dashboard.php'
    
    # Room Teachers - Grade 6
    if 'room teacher grade 6th' in user_type.lower():
        if 'A' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_6A/grade_6A_rt_dashboard.php'
        elif 'B' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_6B/grade_6B_rt_dashboard.php'
        elif 'C' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_6C/grade_6C_rt_dashboard.php'
        elif 'D' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_6D/grade_6D_rt_dashboard.php'
    
    # Room Teachers - Grade 7
    if 'room teacher grade 7th' in user_type.lower():
        if 'A' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_7A/grade_7A_rt_dashboard.php'
        elif 'B' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_7B/grade_7B_rt_dashboard.php'
        elif 'C' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_7C/grade_7C_rt_dashboard.php'
        elif 'D' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_7D/grade_7D_rt_dashboard.php'
    
    # Room Teachers - Grade 8
    if 'room teacher grade 8th' in user_type.lower():
        if 'A' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_8A/grade_8A_rt_dashboard.php'
        elif 'B' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_8B/grade_8B_rt_dashboard.php'
        elif 'C' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_8C/grade_8C_rt_dashboard.php'
        elif 'D' in user_type:
            return 'http://localhost/roster_php/room_teacher/grade_8D/grade_8D_rt_dashboard.php'
    
    # Subject Teachers - Grade 8
    if 'subject teacher grade 8th' in user_type.lower():
        if 'Mathematics' in user_type:
            return 'http://localhost/roster_php/subject_teacher/grade_8_Mathematics/grade_8_Mathematics.php'
        elif 'General Science' in user_type:
            return 'http://localhost/roster_php/subject_teacher/grade_8_Gen_Science/grade_8_Gen_Science.php'
        elif 'Social Science' in user_type:
            return 'http://localhost/roster_php/subject_teacher/grade_8_Soc_Science/grade_8_Soc_Science.php'
        elif 'Amharic' in user_type:
            return 'http://localhost/roster_php/subject_teacher/grade_8_Amharic/grade_8_Amharic.php'
        elif 'English' in user_type:
            return 'http://localhost/roster_php/subject_teacher/grade_8_English/grade_8_English.php'
        elif 'IT' in user_type:
            return 'http://localhost/roster_php/subject_teacher/grade_8_IT/grade_8_IT.php'
        elif 'Arts' in user_type:
            return 'http://localhost/roster_php/subject_teacher/grade_8_Arts/grade_8_Arts.php'
        elif 'HPE' in user_type:
            return 'http://localhost/roster_php/subject_teacher/grade_8_HPE/grade_8_HPE.php'
        elif 'CTE' in user_type:
            return 'http://localhost/roster_php/subject_teacher/grade_8_CTE/grade_8_CTE.php'
    
    # Students
    if 'student' in user_type.lower():
        return 'http://localhost/roster_php/student/student_dashboard.php'
    
    # Parents
    if user_type == 'parent' or user_type == '':
        return 'http://localhost/roster_php/parent/parent_dashboard.php'
    
    # Default
    print(f"WARNING: No mapping found for user_type: {user_type}")
    return 'http://localhost/roster_php/index.php'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template_string(HTML_TEMPLATE, error="Please enter username and password")
        
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT user_id, username, user_type FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user:
                # For testing - accept any password
                # In production, verify password hash here
                
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['user_type'] = user['user_type']
                session['logged_in'] = True
                
                # Update last login
                cursor.execute("UPDATE users SET last_login = NOW() WHERE user_id = %s", (user['user_id'],))
                conn.commit()
                cursor.close()
                conn.close()
                
                dashboard_url = get_dashboard_url(user['user_type'], username)
                print(f"\n✅ LOGIN SUCCESS: {username}")
                print(f"   User Type: {user['user_type']}")
                print(f"   Redirecting to: {dashboard_url}\n")
                
                return redirect(dashboard_url)
            else:
                cursor.close()
                conn.close()
                return render_template_string(HTML_TEMPLATE, error="Invalid username or password")
                
        except Exception as e:
            print(f"ERROR: {e}")
            return render_template_string(HTML_TEMPLATE, error="Database connection error")
    
    return render_template_string(HTML_TEMPLATE, error=None)

@app.route('/')
def index():
    return redirect('/login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🏫 SCHOOL MANAGEMENT SYSTEM - HYBRID LOGIN")
    print("="*70)
    print("\n✅ Flask Login Service: http://127.0.0.1:5000/login")
    print("\n📋 SUPPORTED USER TYPES:")
    print("   • Directors: director, vice director, supervisor, KG director")
    print("   • Room Teachers: Grades 1-8 (A-D/E sections)")
    print("   • Subject Teachers: Grade 8 subjects")
    print("   • Students & Parents")
    print("\n⚠️  REQUIREMENTS:")
    print("   1. XAMPP Apache must be RUNNING (port 80)")
    print("   2. XAMPP MySQL must be RUNNING")
    print("   3. PHP files must be in: C:\\xampp\\htdocs\\roster_php")
    print("\n🔐 Test Logins (from your database):")
    print("   • director001 (director)")
    print("   • TCH-001 (room teacher grade 6th A)")
    print("   • student001 (student)")
    print("\n" + "="*70 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)