import os
from flask import Blueprint, request, session, redirect, url_for, render_template_string
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

# Create blueprint
insert_admin_staff_bp = Blueprint('insert_admin_staff', __name__)

# Constants
ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif']
MAX_PHOTO_SIZE = 1024 * 1024  # 1MB
VALID_ROLES = ['director', 'vice director', 'supervisor', 'KG director']

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add Admin Staff</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 20px;
        }
        .form-row {
            display: flex;
            flex-wrap: wrap;
            margin: 0 -15px;
        }
        .form-column {
            flex: 0 0 50%;
            padding: 0 15px;
            box-sizing: border-box;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"],
        input[type="number"],
        input[type="password"],
        input[type="file"],
        select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .radio-group {
            display: flex;
            gap: 15px;
        }
        .radio-option {
            display: flex;
            align-items: center;
        }
        .form-actions {
            display: flex;
            justify-content: flex-end;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #45a049;
        }
        .error {
            color: #d9534f;
            margin-bottom: 15px;
            padding: 10px;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
        }
        .success {
            color: #5cb85c;
            margin-bottom: 15px;
            padding: 10px;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 4px;
        }
        .photo-preview {
            max-width: 200px;
            max-height: 200px;
            margin-top: 10px;
            display: none;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        @media (max-width: 768px) {
            .form-column {
                flex: 0 0 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Add New Admin Staff</h1>
        
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if success %}
            <div class="success">{{ success }}</div>
        {% endif %}
        
        <form method="POST" enctype="multipart/form-data">
            <div class="form-row">
                <div class="form-column">
                    <div class="form-group">
                        <label for="full_name">Full Name:</label>
                        <input type="text" id="full_name" name="full_name" 
                               value="{{ form_data.full_name }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="age">Age:</label>
                        <input type="number" id="age" name="age" min="18" max="99"
                               value="{{ form_data.age }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="phone">Phone:</label>
                        <input type="text" id="phone" name="phone" 
                               value="{{ form_data.phone }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                </div>
                
                <div class="form-column">
                    <div class="form-group">
                        <label>Gender:</label>
                        <div class="radio-group">
                            <div class="radio-option">
                                <input type="radio" id="male" name="gender" value="M" 
                                       {{ 'checked' if form_data.gender == 'M' else '' }} required>
                                <label for="male">Male</label>
                            </div>
                            <div class="radio-option">
                                <input type="radio" id="female" name="gender" value="F" 
                                       {{ 'checked' if form_data.gender == 'F' else '' }}>
                                <label for="female">Female</label>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="role">Role:</label>
                        <select id="role" name="role" required>
                            <option value="director" {{ 'selected' if form_data.role == 'director' else '' }}>Director</option>
                            <option value="vice director" {{ 'selected' if form_data.role == 'vice director' else '' }}>Vice Director</option>
                            <option value="supervisor" {{ 'selected' if form_data.role == 'supervisor' else '' }}>Supervisor</option>
                            <option value="KG director" {{ 'selected' if form_data.role == 'KG director' else '' }}>KG Director</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" 
                               value="{{ form_data.username }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="photo">Profile Photo (max 1MB, JPG/PNG/GIF):</label>
                        <input type="file" id="photo" name="photo" accept="image/jpeg,image/png,image/gif">
                        <img id="photoPreview" class="photo-preview" alt="Photo preview">
                    </div>
                </div>
            </div>
            
            <div class="form-actions">
                <button type="submit">Add Admin Staff</button>
            </div>
        </form>
    </div>

    <script>
        document.getElementById('photo').addEventListener('change', function(e) {
            const preview = document.getElementById('photoPreview');
            const file = e.target.files[0];
            
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                }
                reader.readAsDataURL(file);
            } else {
                preview.src = '#';
                preview.style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

@insert_admin_staff_bp.route('/director/insert_admin_staff', methods=['GET', 'POST'])
def insert_admin_staff():
    """Add Admin Staff - MySQL version"""
    
    # Check if user is logged in as director
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return redirect(url_for('unauthorized'))
    
    # Initialize variables
    success = ''
    error = ''
    form_data = {
        'full_name': '',
        'gender': 'M',
        'age': '',
        'role': 'director',
        'phone': '',
        'username': '',
        'password': '',
        'photo': None,
        'photo_name': ''
    }
    
    # Process form submission
    if request.method == 'POST':
        try:
            # Process photo upload
            photo_data = None
            photo_name = ''
            
            if 'photo' in request.files and request.files['photo'].filename:
                photo_file = request.files['photo']
                
                # Validate photo
                if photo_file.content_type not in ALLOWED_TYPES:
                    raise Exception("Only JPG, PNG, and GIF images are allowed.")
                
                photo_file.seek(0, os.SEEK_END)
                file_size = photo_file.tell()
                photo_file.seek(0)
                
                if file_size > MAX_PHOTO_SIZE:
                    raise Exception("Image size must be less than 1MB.")
                
                photo_name = secure_filename(photo_file.filename)
                photo_data = photo_file.read()
            
            # Get form data
            form_data = {
                'full_name': request.form.get('full_name', '').strip(),
                'gender': request.form.get('gender', 'M'),
                'age': request.form.get('age', ''),
                'role': request.form.get('role', 'director'),
                'phone': request.form.get('phone', '').strip(),
                'username': request.form.get('username', '').strip(),
                'password': request.form.get('password', ''),
                'photo': photo_data,
                'photo_name': photo_name
            }
            
            # Validate required fields
            required_fields = ['full_name', 'gender', 'age', 'role', 'phone', 'username', 'password']
            for field in required_fields:
                if not form_data[field]:
                    raise Exception("Please fill in all required fields")
            
            # Convert age to integer
            form_data['age'] = int(form_data['age'])
            
            # Validate role
            if form_data['role'] not in VALID_ROLES:
                raise Exception("Invalid role selected")
            
            # Get database connection
            from app import get_db
            conn = get_db()
            cursor = conn.cursor()
            
            try:
                # Check username availability
                cursor.execute("SELECT username FROM users WHERE username = %s", (form_data['username'],))
                if cursor.fetchone():
                    raise Exception("Username already exists")
                
                # Insert into admin_staff table
                cursor.execute("""
                    INSERT INTO admin_staff (full_name, gender, age, role, phone, photo, photo_name) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    form_data['full_name'],
                    form_data['gender'],
                    form_data['age'],
                    form_data['role'],
                    form_data['phone'],
                    photo_data,
                    photo_name
                ))
                
                admin_id = cursor.lastrowid
                
                # Insert into users table
                hashed_password = generate_password_hash(form_data['password'])
                cursor.execute("""
                    INSERT INTO users (username, password_hash, user_type, reference_id, account_status) 
                    VALUES (%s, %s, 'admin_staff', %s, 'active')
                """, (form_data['username'], hashed_password, admin_id))
                
                conn.commit()
                
                success = "Admin staff added successfully!"
                
                # Reset form data
                form_data = {
                    'full_name': '',
                    'gender': 'M',
                    'age': '',
                    'role': 'director',
                    'phone': '',
                    'username': '',
                    'password': '',
                    'photo': None,
                    'photo_name': ''
                }
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                conn.close()
                
        except Exception as e:
            error = str(e)
    
    # Render template
    return render_template_string(
        HTML_TEMPLATE,
        success=success,
        error=error,
        form_data=form_data
    )

print("✅ insert_admin_staff.py loaded successfully")