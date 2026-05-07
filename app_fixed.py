from flask import Flask, render_template_string, session, redirect, request
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
app = Flask(__name__)
app.secret_key = 'your-secret-key'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

# Import the fixed director dashboard
from director.director_dashboard_fixed import director_dashboard_bp
app.register_blueprint(director_dashboard_bp)
print("✅ Director dashboard registered at /director/director_dashboard")

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Login</title>
<style>
body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);display:flex;justify-content:center;align-items:center;height:100vh}
.login-container{background:white;padding:40px;border-radius:10px;width:350px}
h2{text-align:center}
input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd}
button{width:100%;padding:12px;background:#667eea;color:white;border:none;cursor:pointer}
.error{color:red;background:#ffe6e6;padding:10px;margin-bottom:20px}
</style>
</head>
<body>
<div class="login-container">
<h2>School Login</h2>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="POST">
<input type="text" name="username" placeholder="Username" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">Login</button>
</form>
</div>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, username, user_type FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            session['logged_in'] = True
            print(f"✅ Login: {username} -> /director/director_dashboard")
            return redirect('/director/director_dashboard')
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Invalid username")
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/')
def index():
    return redirect('/login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    print("\n" + "="*50)
    print("SCHOOL MANAGEMENT SYSTEM")
    print("="*50)
    print("URL: http://127.0.0.1:5000/login")
    print("Test: director001 (any password)")
    print("="*50 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)