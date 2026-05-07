# ==============================================
# Insert Teacher - Complete Python Conversion
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
from datetime import datetime

director_insert_teacher = Blueprint('director_insert_teacher', __name__, url_prefix='/director')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        if session.get('user_type') != 'director':
            return redirect('/unauthorized')
        return f(*args, **kwargs)
    return decorated_function

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db():
    return mysql.connector.connect(**db_config)

@director_insert_teacher.route('/insert_teacher', methods=['GET', 'POST'])
@login_required
def insert_teacher_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    message = None
    message_type = None
    form_data = {}
    
    if request.method == 'POST':
        t_id = request.form.get('t_id', '').strip()
        name = request.form.get('name', '').strip()
        gender = request.form.get('gender', '').strip()
        age = request.form.get('age', '')
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        doj = request.form.get('doj', '').strip()
        teacher_type = request.form.get('teacher_type', '').strip()
        status = request.form.get('status', 'active')
        
        form_data = {
            't_id': t_id, 'name': name, 'gender': gender, 'age': age,
            'phone': phone, 'email': email, 'address': address,
            'doj': doj, 'teacher_type': teacher_type, 'status': status
        }
        
        if not t_id or not name:
            message = "Teacher ID and Name are required"
            message_type = "danger"
        else:
            try:
                cursor.execute("""
                    INSERT INTO teacher (t_id, name, gender, age, phone, email, address, doj, type, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (t_id, name, gender, age, phone, email, address, doj, teacher_type, status))
                conn.commit()
                message = f"Teacher '{name}' registered successfully!"
                message_type = "success"
                form_data = {}
            except Exception as e:
                message = f"Error: {e}"
                message_type = "danger"
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Register Teacher</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        <style>
            .form-container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            }
            .form-title {
                font-size: 1.4rem;
                font-weight: 600;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e9ecef;
            }
            .form-section {
                font-size: 1rem;
                font-weight: 600;
                margin: 15px 0 12px 0;
                padding-left: 10px;
                border-left: 3px solid #667eea;
            }
            .form-group {
                margin-bottom: 12px;
            }
            .form-label {
                font-size: 12px;
                font-weight: 500;
                margin-bottom: 4px;
            }
            .form-control, .form-select {
                padding: 6px 10px;
                font-size: 13px;
            }
            .required:after {
                content: " *";
                color: #dc3545;
            }
        </style>
    </head>
    <body>
        <div class="container py-3">
            <div class="form-container">
                <div class="form-title">
                    <i class="fas fa-chalkboard-teacher"></i> Register New Teacher
                </div>
                
                <a href="/director/director_dashboard" class="btn btn-secondary btn-sm mb-3">
                    <i class="fas fa-arrow-left"></i> Back
                </a>
                
                {% if message %}
                    <div class="alert alert-{{ message_type }}">{{ message }}</div>
                {% endif %}
                
                <form method="POST">
                    <div class="form-section">Basic Information</div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label required">Teacher ID</label>
                                <input type="text" class="form-control" name="t_id" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label required">Full Name</label>
                                <input type="text" class="form-control" name="name" required>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Gender</label>
                                <select class="form-select" name="gender">
                                    <option value="">Select</option>
                                    <option value="M">Male</option>
                                    <option value="F">Female</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Age</label>
                                <input type="number" class="form-control" name="age">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Join Date</label>
                                <input type="date" class="form-control" name="doj">
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-section">Contact Information</div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Phone</label>
                                <input type="text" class="form-control" name="phone">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" name="email">
                            </div>
                        </div>
                        <div class="col-md-12">
                            <div class="form-group">
                                <label class="form-label">Address</label>
                                <input type="text" class="form-control" name="address">
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-section">Professional Information</div>
                    <div class="row">
                        <div class="col-md-8">
                            <div class="form-group">
                                <label class="form-label">Teacher Type</label>
                                <select class="form-select" name="teacher_type">
                                    <option value="">Select Type</option>
                                    <option value="room teacher">Room Teacher</option>
                                    <option value="subject teacher">Subject Teacher</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Status</label>
                                <select class="form-select" name="status">
                                    <option value="active">Active</option>
                                    <option value="inactive">Inactive</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary w-100 mt-3">
                        <i class="fas fa-save"></i> Register Teacher
                    </button>
                </form>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    message=message,
    message_type=message_type,
    form_data=form_data
    )