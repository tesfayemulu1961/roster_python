# ==============================================
# Insert Class - Complete Python Conversion
# Converted from insert_class.php
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector

director_insert_class = Blueprint('director_insert_class', __name__, url_prefix='/director')

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

@director_insert_class.route('/insert_class', methods=['GET', 'POST'])
@login_required
def insert_class_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    message = None
    message_type = None
    
    # Fetch sections and teachers for dropdowns
    cursor.execute("SELECT ID, sec_name FROM section ORDER BY sec_name")
    sections = cursor.fetchall()
    
    cursor.execute("""
        SELECT ta.ID, t.name as teacher_name 
        FROM teacher_assignment ta
        JOIN teacher t ON ta.teacher_id = t.ID
        ORDER BY t.name
    """)
    teacher_assignments = cursor.fetchall()
    
    if request.method == 'POST':
        class_name = request.form.get('class_name', '').strip()
        section_id = request.form.get('section_id', '')
        teacher_assignment_id = request.form.get('teacher_assignment_id', '')
        
        if not class_name or not section_id or not teacher_assignment_id:
            message = "Error: Please fill all required fields"
            message_type = "danger"
        else:
            try:
                cursor.execute("""
                    INSERT INTO class (class_name, section_id, teacher_assignment_id) 
                    VALUES (%s, %s, %s)
                """, (class_name, section_id, teacher_assignment_id))
                conn.commit()
                message = f"Class '{class_name}' added successfully!"
                message_type = "success"
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
        <title>Insert Class - Director Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        <style>
            .form-container {
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <div class="container py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="fas fa-plus-circle"></i> Insert New Class</h2>
                <a href="/director/director_dashboard" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i> Back to Dashboard
                </a>
            </div>
            
            <div class="form-container">
                {% if message %}
                    <div class="alert alert-{{ message_type }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endif %}
                
                <form method="POST">
                    <div class="mb-3">
                        <label for="class_name" class="form-label">Class Name <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" id="class_name" name="class_name" required 
                               placeholder="e.g., Grade 6A, Grade 7B, KG-1A, etc.">
                    </div>
                    
                    <div class="mb-3">
                        <label for="section_id" class="form-label">Select Section <span class="text-danger">*</span></label>
                        <select class="form-control" id="section_id" name="section_id" required>
                            <option value="">-- Select Section --</option>
                            {% for section in sections %}
                                <option value="{{ section.ID }}">Section {{ section.sec_name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label for="teacher_assignment_id" class="form-label">Assign Teacher <span class="text-danger">*</span></label>
                        <select class="form-control" id="teacher_assignment_id" name="teacher_assignment_id" required>
                            <option value="">-- Select Teacher --</option>
                            {% for teacher in teacher_assignments %}
                                <option value="{{ teacher.ID }}">{{ teacher.teacher_name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="fas fa-save"></i> Insert Class
                    </button>
                </form>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    sections=sections,
    teacher_assignments=teacher_assignments,
    message=message,
    message_type=message_type
    )