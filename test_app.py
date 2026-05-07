from flask import Flask, session, redirect, request, render_template_string

app = Flask(__name__)
app.secret_key = 'test-key'

# Simple login page
LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Test Login</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; justify-content: center; align-items: center; height: 100vh; }
        .box { background: white; padding: 40px; border-radius: 10px; width: 300px; }
        input, button { width: 100%; padding: 10px; margin: 10px 0; }
        button { background: #667eea; color: white; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Test Login</h2>
        {% if error %}<p style="color:red">{{ error }}</p>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p style="font-size:12px; margin-top:20px;">Test: director001 (any password)</p>
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        
        # Simple test - if username is director001, redirect to director dashboard
        if username == 'director001':
            session['user_type'] = 'director'
            session['username'] = username
            session['logged_in'] = True
            print(f"Redirecting to: /director/director_dashboard")
            return redirect('/director/director_dashboard')
        else:
            return render_template_string(LOGIN_PAGE, error="Invalid username")
    
    return render_template_string(LOGIN_PAGE)

# Direct route for director dashboard
@app.route('/director/director_dashboard')
def director_dashboard():
    if not session.get('logged_in'):
        return redirect('/login')
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Director Dashboard</title>
        <style>
            body { font-family: Arial; margin: 0; padding: 20px; background: #f4f4f4; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; }
            button { background: #e74c3c; color: white; padding: 10px 20px; border: none; cursor: pointer; }
            .content { padding: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 Director Dashboard</h1>
            <button onclick="location.href='/logout'">Logout</button>
        </div>
        <div class="content">
            <h2>Welcome Director!</h2>
            <p>This is the correct director dashboard!</p>
            <p>If you see this, the redirect is working correctly.</p>
        </div>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    print("\n" + "="*60)
    print("TEST APP - Run this first")
    print("="*60)
    print("URL: http://127.0.0.1:5000/login")
    print("Test: director001 (any password)")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)