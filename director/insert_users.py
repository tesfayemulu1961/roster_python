from flask import Blueprint, request, session, redirect, url_for, render_template_string, jsonify
from werkzeug.security import generate_password_hash
import mysql.connector

# Create blueprint
insert_users_bp = Blueprint('insert_users', __name__)

# Database configuration (use your existing config)
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def get_reference_options(user_type):
    """Get reference options based on user type"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    options = []
    
    try:
        if 'director' in user_type or 'vice director' in user_type or 'supervisor' in user_type or 'KG director' in user_type:
            # Admin staff
            cursor.execute("SELECT ID, full_name, role FROM admin_staff")
            rows = cursor.fetchall()
            for row in rows:
                options.append({
                    'id': row['ID'],
                    'text': f"{row['ID']} - {row['full_name']} ({row['role']})"
                })
        
        elif 'teacher' in user_type:
            # Teachers
            cursor.execute("SELECT ID, name, type FROM teacher")
            rows = cursor.fetchall()
            for row in rows:
                options.append({
                    'id': row['ID'],
                    'text': f"{row['ID']} - {row['name']} ({row['type']})"
                })
        
        elif 'student' in user_type:
            # Students
            cursor.execute("SELECT RN, fullname, grade_id, section_id FROM student")
            rows = cursor.fetchall()
            for row in rows:
                options.append({
                    'id': row['RN'],
                    'text': f"{row['RN']} - {row['fullname']} (Grade {row['grade_id']} - Section {row['section_id']})"
                })
        
        elif 'parent' in user_type:
            # Parents
            cursor.execute("""
                SELECT p.ID, p.p_name, s.fullname as student_name 
                FROM parent p 
                JOIN student s ON p.student_RN = s.RN
            """)
            rows = cursor.fetchall()
            for row in rows:
                options.append({
                    'id': row['ID'],
                    'text': f"{row['ID']} - {row['p_name']} (Parent of {row['student_name']})"
                })
    finally:
        cursor.close()
        conn.close()
    
    return options

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add New User</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
        }
        input[type="text"],
        input[type="password"],
        input[type="number"],
        select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .btn-submit {
            background-color: #4CAF50;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
            margin-top: 10px;
        }
        .btn-submit:hover {
            background-color: #45a049;
        }
        .status-select {
            display: flex;
            gap: 15px;
        }
        .status-select label {
            display: flex;
            align-items: center;
            gap: 5px;
            font-weight: normal;
        }
        .alert {
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 4px;
        }
        .alert-success {
            background-color: #dff0d8;
            color: #3c763d;
            border: 1px solid #d6e9c6;
        }
        .alert-error {
            background-color: #f2dede;
            color: #a94442;
            border: 1px solid #ebccd1;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Add New User Account</h1>
        
        {% if success %}
            <div class="alert alert-success">{{ success }}</div>
        {% endif %}
        
        {% if error %}
            <div class="alert alert-error">{{ error }}</div>
        {% endif %}
        
        <form method="POST" id="userForm">
            <div class="form-group">
                <label for="reference_id">Reference:</label>
                <select id="reference_id" name="reference_id" required>
                    <option value="">Select a reference</option>
                    {% if reference_options %}
                        {% for option in reference_options %}
                            <option value="{{ option.id }}" {% if form_data.reference_id == option.id %}selected{% endif %}>
                                {{ option.text }}
                            </option>
                        {% endfor %}
                    {% endif %}
                </select>
            </div>
            
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" value="{{ form_data.username }}" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <div class="form-group">
                <label for="user_type">User Type:</label>
                <select id="user_type" name="user_type" required>
                    <option value="">Select User Type</option>
                    <optgroup label="Directors">
                        <option value="director" {% if form_data.user_type == 'director' %}selected{% endif %}>Director</option>
                        <option value="vice director" {% if form_data.user_type == 'vice director' %}selected{% endif %}>Vice Director</option>
                        <option value="supervisor" {% if form_data.user_type == 'supervisor' %}selected{% endif %}>Supervisor</option>
                    </optgroup>
                    
                    {# Room Teachers Grades 1-8 and KG #}
                    {% for grade in ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th'] %}
                    <optgroup label="Room Teachers grade {{ grade }}">
                        {% for section in ['A', 'B', 'C', 'D'] %}
                        <option value="room teacher grade {{ grade }} {{ section }}" {% if form_data.user_type == 'room teacher grade ' ~ grade ~ ' ' ~ section %}selected{% endif %}>
                            Room Teacher Grade {{ grade }} {{ section }}
                        </option>
                        {% endfor %}
                    </optgroup>
                    {% endfor %}
                    
                    <optgroup label="Room Teachers KG-1">
                        {% for section in ['A', 'B', 'C', 'D'] %}
                        <option value="room teacher KG-1 {{ section }}" {% if form_data.user_type == 'room teacher KG-1 ' ~ section %}selected{% endif %}>Room Teacher KG-1 {{ section }}</option>
                        {% endfor %}
                    </optgroup>
                    <optgroup label="Room Teachers KG-2">
                        {% for section in ['A', 'B', 'C', 'D'] %}
                        <option value="room teacher KG-2 {{ section }}" {% if form_data.user_type == 'room teacher KG-2 ' ~ section %}selected{% endif %}>Room Teacher KG-2 {{ section }}</option>
                        {% endfor %}
                    </optgroup>
                    <optgroup label="Room Teachers KG-3">
                        {% for section in ['A', 'B', 'C', 'D'] %}
                        <option value="room teacher KG-3 {{ section }}" {% if form_data.user_type == 'room teacher KG-3 ' ~ section %}selected{% endif %}>Room Teacher KG-3 {{ section }}</option>
                        {% endfor %}
                    </optgroup>
                </select>
            </div>
            
            <div class="form-group">
                <label>Account Status:</label>
                <div class="status-select">
                    <label><input type="radio" name="account_status" value="active" {% if form_data.account_status == 'active' %}checked{% endif %}> Active</label>
                    <label><input type="radio" name="account_status" value="inactive" {% if form_data.account_status == 'inactive' %}checked{% endif %}> Inactive</label>
                    <label><input type="radio" name="account_status" value="suspended" {% if form_data.account_status == 'suspended' %}checked{% endif %}> Suspended</label>
                </div>
            </div>
            
            <button type="submit" class="btn-submit">Create User Account</button>
        </form>
    </div>
    
    <script>
        document.getElementById('user_type').addEventListener('change', function() {
            const userType = this.value;
            const referenceSelect = document.getElementById('reference_id');
            
            if (userType) {
                referenceSelect.innerHTML = '<option value="">Loading...</option>';
                
                fetch('/get_reference_options', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: 'user_type=' + encodeURIComponent(userType)
                })
                .then(response => response.json())
                .then(data => {
                    referenceSelect.innerHTML = '<option value="">Select a reference</option>';
                    if (data.length > 0) {
                        data.forEach(option => {
                            referenceSelect.innerHTML += `<option value="${option.id}">${option.text}</option>`;
                        });
                    } else {
                        referenceSelect.innerHTML = '<option value="">No references found</option>';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    referenceSelect.innerHTML = '<option value="">Error loading data</option>';
                });
            } else {
                referenceSelect.innerHTML = '<option value="">Select a reference</option>';
            }
        });
    </script>
</body>
</html>
"""

@insert_users_bp.route('/director/insert_users', methods=['GET', 'POST'])
def insert_users():
    """Add New User Account"""
    
    # Check if user is logged in as director
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return redirect(url_for('unauthorized'))
    
    error = ''
    success = ''
    form_data = {
        'username': '',
        'password': '',
        'user_type': '',
        'reference_id': '',
        'account_status': 'active'
    }
    reference_options = []
    
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user_type = request.form.get('user_type', '')
        reference_id = request.form.get('reference_id', '')
        account_status = request.form.get('account_status', 'active')
        
        # Validate inputs
        if not username or not password or not user_type or not reference_id:
            error = "All fields are required."
        else:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            try:
                # Check if username already exists
                cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    error = "Username already exists. Please choose a different username."
                else:
                    # Hash the password
                    password_hash = generate_password_hash(password)
                    
                    # Insert new user
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, user_type, reference_id, account_status) 
                        VALUES (%s, %s, %s, %s, %s)
                    """, (username, password_hash, user_type, reference_id, account_status))
                    
                    conn.commit()
                    success = "User account created successfully!"
                    
                    # Clear form fields on success
                    form_data = {
                        'username': '',
                        'password': '',
                        'user_type': '',
                        'reference_id': '',
                        'account_status': 'active'
                    }
                    
            except Exception as e:
                error = f"Database error: {str(e)}"
                conn.rollback()
            finally:
                cursor.close()
                conn.close()
        
        # Set form data for re-display
        if error:
            form_data = {
                'username': username,
                'password': '',
                'user_type': user_type,
                'reference_id': reference_id,
                'account_status': account_status
            }
            # Get reference options for the selected user type
            if user_type:
                reference_options = get_reference_options(user_type)
    
    # For GET request, get reference options if user_type is selected
    elif request.method == 'GET' and request.args.get('user_type'):
        form_data['user_type'] = request.args.get('user_type')
        reference_options = get_reference_options(form_data['user_type'])
    
    return render_template_string(
        HTML_TEMPLATE,
        success=success,
        error=error,
        form_data=form_data,
        reference_options=reference_options
    )


@insert_users_bp.route('/get_reference_options', methods=['POST'])
def get_reference_options_ajax():
    """AJAX endpoint to get reference options"""
    user_type = request.form.get('user_type', '')
    options = get_reference_options(user_type)
    return jsonify(options)


print("✅ insert_users.py blueprint loaded")
print("   📌 Routes:")
print("      - /director/insert_users")
print("      - /get_reference_options (AJAX)")