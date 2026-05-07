from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db():
    return mysql.connector.connect(**db_config)

@app.route('/')
def home():
    return jsonify({
        'message': 'Roster System API',
        'status': 'running',
        'endpoints': ['/login', '/users', '/students', '/teachers']
    })

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT user_id, username, user_type FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if user:
        return jsonify({
            'success': True,
            'message': f'Welcome {username}!',
            'user': user
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid username'
        }), 401

@app.route('/users')
def get_users():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, username, user_type FROM users LIMIT 100")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)

@app.route('/students')
def get_students():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT RN, studid, fullname, grade, section FROM student LIMIT 100")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(students)

@app.route('/teachers')
def get_teachers():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, phone FROM teacher LIMIT 100")
    teachers = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(teachers)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("SIMPLE ROSTER API - WORKING VERSION")
    print("="*50)
    print("Server: http://127.0.0.1:5000")
    print("\nTest these commands:")
    print("  curl http://127.0.0.1:5000/")
    print("  curl http://127.0.0.1:5000/users")
    print("\nLogin test:")
    print('  curl -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d "{\\"username\\":\\"director001\\",\\"password\\":\\"anything\\"}"')
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)