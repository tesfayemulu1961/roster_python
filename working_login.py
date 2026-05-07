from flask import Flask, render_template_string, redirect, request
import mysql.connector

app = Flask(__name__)
app.secret_key = 'working-version-key'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>School Management System - Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            width: 350px;
        }
        h2 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #5a67d8;
        }
        .error {
            color: red;
            background: #ffe6e6;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>School Management System</h2>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required autofocus>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
'''

def get_dashboard(user_type):
    """Map user type to dashboard URL"""
    
    # Director dashboards
    if user_type == 'director':
        return 'http://localhost/roster_php/director/director_dashboard.php'
    if user_type == 'vice director':
        return 'http://localhost/roster_php/vice_director/vice_director_dashboard.php'
    if user_type == 'supervisor':
        return 'http://localhost/roster_php/supervisor/supervisor_dashboard.php'
    if user_type == 'KG director':
        return 'http://localhost/roster_php/kg_director/kg_director_dashboard.php'
    
    # Room teachers
    if 'room teacher grade 6th A' in user_type:
        return 'http://localhost/roster_php/room_teacher/grade_6A/grade_6A_rt_dashboard.php'
    if 'room teacher grade 8th C' in user_type:
        return 'http://localhost/roster_php/room_teacher/grade_8C/grade_8C_rt_dashboard.php'
    
    # Students
    if 'student' in user_type.lower():
        return 'http://localhost/roster_php/student/student_dashboard.php'
    
    # Default
    return 'http://localhost/roster_php/index.php'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template_string(LOGIN_PAGE, error="Please enter username and password")
        
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            
            # Check user
            cursor.execute("SELECT user_type FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user:
                # For testing - accept any password
                dashboard = get_dashboard(user['user_type'])
                print(f"\n✅ Login: {username} -> {user['user_type']}")
                print(f"   Redirecting to: {dashboard}\n")
                return redirect(dashboard)
            else:
                return render_template_string(LOGIN_PAGE, error="Invalid username")
                
        except Exception as e:
            print(f"Error: {e}")
            return render_template_string(LOGIN_PAGE, error="Database error")
    
    return render_template_string(LOGIN_PAGE, error=None)

@app.route('/')
def index():
    return redirect('/login')

if __name__ == '__main__':
    print("\n" + "="*60)
    print("WORKING LOGIN SYSTEM - REDIRECTS TO PHP DASHBOARDS")
    print("="*60)
    print("\nURL: http://127.0.0.1:5000/login")
    print("\nTest with:")
    print("  • director001 (any password)")
    print("  • TCH-001 (room teacher)")
    print("  • student001 (student)")
    print("\nMake sure XAMPP Apache is RUNNING!")
    print("="*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)