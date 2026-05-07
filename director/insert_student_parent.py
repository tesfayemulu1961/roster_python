# ==============================================
# Insert Student & Parent - Compact Narrow Form
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector

director_insert_student_parent = Blueprint('director_insert_student_parent', __name__, url_prefix='/director')

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

@director_insert_student_parent.route('/insert_student_parent', methods=['GET', 'POST'])
@login_required
def insert_student_parent_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    message = None
    message_type = None
    form_data = {}
    
    # Get grades and sections for dropdowns
    try:
        cursor.execute("SELECT ID, level FROM grade ORDER BY ID")
        grades = cursor.fetchall()
    except:
        grades = []
    
    try:
        cursor.execute("SELECT ID, sec_name FROM section ORDER BY sec_name")
        sections = cursor.fetchall()
    except:
        sections = []
    
    if request.method == 'POST':
        # Get form data
        student_first_name = request.form.get('student_first_name', '').strip()
        student_last_name = request.form.get('student_last_name', '').strip()
        student_email = request.form.get('student_email', '').strip()
        student_phone = request.form.get('student_phone', '').strip()
        student_gender = request.form.get('student_gender', '').strip()
        student_grade_id = request.form.get('student_grade_id', '')
        student_section_id = request.form.get('student_section_id', '')
        student_roll_number = request.form.get('student_roll_number', '').strip()
        
        parent_first_name = request.form.get('parent_first_name', '').strip()
        parent_last_name = request.form.get('parent_last_name', '').strip()
        parent_email = request.form.get('parent_email', '').strip()
        parent_phone = request.form.get('parent_phone', '').strip()
        parent_address = request.form.get('parent_address', '').strip()
        
        form_data = {
            'student_first_name': student_first_name,
            'student_last_name': student_last_name,
            'student_email': student_email,
            'student_phone': student_phone,
            'student_gender': student_gender,
            'parent_first_name': parent_first_name,
            'parent_last_name': parent_last_name,
            'parent_email': parent_email,
            'parent_phone': parent_phone,
            'parent_address': parent_address
        }
        
        if not student_first_name or not student_last_name:
            message = "Student first and last name required"
            message_type = "danger"
        elif not parent_first_name or not parent_last_name:
            message = "Parent first and last name required"
            message_type = "danger"
        else:
            try:
                cursor.execute("""
                    INSERT INTO parent (first_name, last_name, email, phone, address)
                    VALUES (%s, %s, %s, %s, %s)
                """, (parent_first_name, parent_last_name, parent_email, parent_phone, parent_address))
                parent_id = cursor.lastrowid
                
                cursor.execute("""
                    INSERT INTO student (first_name, last_name, email, phone, gender, 
                                        grade_id, section_id, roll_number, parent_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (student_first_name, student_last_name, student_email, student_phone,
                      student_gender, student_grade_id or None, student_section_id or None,
                      student_roll_number, parent_id))
                
                conn.commit()
                message = "✓ Student registered successfully!"
                message_type = "success"
                form_data = {}
                
            except Exception as e:
                conn.rollback()
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
        <title>Register Student & Parent</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        <style>
            .form-container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 20px 25px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            }
            .form-title {
                font-size: 1.4rem;
                font-weight: 600;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e9ecef;
                color: #2c3e50;
            }
            .form-title i {
                color: #667eea;
                margin-right: 8px;
            }
            .section-title {
                font-size: 1rem;
                font-weight: 600;
                margin: 15px 0 12px 0;
                padding-left: 10px;
                border-left: 3px solid #667eea;
                color: #495057;
            }
            .form-group {
                margin-bottom: 12px;
            }
            .form-label {
                font-size: 12px;
                font-weight: 500;
                margin-bottom: 4px;
                color: #495057;
            }
            .form-control, .form-select {
                padding: 6px 10px;
                font-size: 13px;
                border-radius: 6px;
                border: 1px solid #dee2e6;
            }
            .form-control:focus, .form-select:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 2px rgba(102,126,234,0.1);
            }
            .required:after {
                content: " *";
                color: #dc3545;
            }
            .btn-submit {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
                border: none;
                border-radius: 8px;
                width: 100%;
                margin-top: 10px;
            }
            .btn-submit:hover {
                opacity: 0.9;
                transform: translateY(-1px);
            }
            .alert {
                padding: 10px 15px;
                font-size: 13px;
                border-radius: 8px;
            }
            .row {
                margin-left: -8px;
                margin-right: -8px;
            }
            .row > [class*="col-"] {
                padding-left: 8px;
                padding-right: 8px;
            }
        </style>
    </head>
    <body>
        <div class="container py-3">
            <div class="form-container">
                <div class="form-title">
                    <i class="fas fa-user-plus"></i> Register Student & Parent
                </div>
                
                <a href="/director/director_dashboard" class="btn btn-secondary btn-sm mb-3">
                    <i class="fas fa-arrow-left"></i> Back to Dashboard
                </a>
                
                {% if message %}
                    <div class="alert alert-{{ message_type }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endif %}
                
                <form method="POST">
                    <!-- Student Section -->
                    <div class="section-title">
                        <i class="fas fa-user-graduate"></i> Student Information
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label required">First Name</label>
                                <input type="text" class="form-control" name="student_first_name" 
                                       value="{{ form_data.get('student_first_name', '') }}" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label required">Last Name</label>
                                <input type="text" class="form-control" name="student_last_name" 
                                       value="{{ form_data.get('student_last_name', '') }}" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" name="student_email" 
                                       value="{{ form_data.get('student_email', '') }}">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Phone</label>
                                <input type="text" class="form-control" name="student_phone" 
                                       value="{{ form_data.get('student_phone', '') }}">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Gender</label>
                                <select class="form-select" name="student_gender">
                                    <option value="">Select</option>
                                    <option value="Male">Male</option>
                                    <option value="Female">Female</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Roll Number</label>
                                <input type="text" class="form-control" name="student_roll_number" 
                                       value="{{ form_data.get('student_roll_number', '') }}">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="form-group">
                                <label class="form-label">Grade</label>
                                <select class="form-select" name="student_grade_id">
                                    <option value="">Select</option>
                                    {% for grade in grades %}
                                        <option value="{{ grade.ID }}">{{ grade.level }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        <div class="col-md-12">
                            <div class="form-group">
                                <label class="form-label">Section</label>
                                <select class="form-select" name="student_section_id">
                                    <option value="">Select</option>
                                    {% for section in sections %}
                                        <option value="{{ section.ID }}">Section {{ section.sec_name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Parent Section -->
                    <div class="section-title">
                        <i class="fas fa-user-friends"></i> Parent/Guardian Information
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label required">First Name</label>
                                <input type="text" class="form-control" name="parent_first_name" 
                                       value="{{ form_data.get('parent_first_name', '') }}" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label required">Last Name</label>
                                <input type="text" class="form-control" name="parent_last_name" 
                                       value="{{ form_data.get('parent_last_name', '') }}" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" name="parent_email" 
                                       value="{{ form_data.get('parent_email', '') }}">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label class="form-label">Phone</label>
                                <input type="text" class="form-control" name="parent_phone" 
                                       value="{{ form_data.get('parent_phone', '') }}">
                            </div>
                        </div>
                        <div class="col-md-12">
                            <div class="form-group">
                                <label class="form-label">Address</label>
                                <textarea class="form-control" name="parent_address" rows="2">{{ form_data.get('parent_address', '') }}</textarea>
                            </div>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-submit">
                        <i class="fas fa-save"></i> Register Student & Parent
                    </button>
                </form>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    grades=grades,
    sections=sections,
    message=message,
    message_type=message_type,
    form_data=form_data
    )