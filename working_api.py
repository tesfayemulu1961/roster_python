from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Empty password for XAMPP
    'database': 'roster'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def home():
    return jsonify({
        'message': 'Roster API is running',
        'status': 'online',
        'database': 'roster'
    })

@app.route('/api/users')
def get_users():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, username, user_type, email FROM users LIMIT 50")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(users)

@app.route('/api/students')
def get_students():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT student_id, name, grade, section FROM student LIMIT 50")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(students)

@app.route('/api/teachers')
def get_teachers():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, phone FROM teacher LIMIT 50")
    teachers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(teachers)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, username, user_type FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user:
        # In a real app, verify password hash here
        # For now, just check if user exists
        return jsonify({
            'message': 'Login successful',
            'user': user,
            'token': 'fake-token-for-now'
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    print("=" * 50)
    print("Simple Roster API Server")
    print("=" * 50)
    print("Database: roster")
    print("Server: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000)