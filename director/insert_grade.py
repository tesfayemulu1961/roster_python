# ==============================================
# Insert Grade - Complete Python Conversion
# Converted from insert_grade.php
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector

# Create blueprint
director_insert_grade = Blueprint('director_insert_grade', __name__, url_prefix='/director')

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

@director_insert_grade.route('/insert_grade', methods=['GET', 'POST'])
@login_required
def insert_grade_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    message = None
    message_type = None
    
    # Handle form submission
    if request.method == 'POST':
        level = request.form.get('level', '').strip()
        section_id = request.form.get('section_id', '')
        teacher_assignment_id = request.form.get('teacher_assignment_id', '')
        
        if not level or not section_id or not teacher_assignment_id:
            message = "Error: Missing required fields"
            message_type = "error"
        else:
            try:
                # Insert grade into database
                cursor.execute("""
                    INSERT INTO grade (level, section_id, teacher_assignment_id) 
                    VALUES (%s, %s, %s)
                """, (level, section_id, teacher_assignment_id))
                conn.commit()
                message = "Grade added successfully."
                message_type = "success"
            except Exception as e:
                message = f"Error: {e}"
                message_type = "error"
    
    # Fetch DISTINCT sections (no duplicates) - Only get unique section names
    cursor.execute("""
        SELECT DISTINCT sec_name 
        FROM section 
        WHERE sec_name IS NOT NULL AND sec_name != ''
        ORDER BY sec_name
    """)
    sections = cursor.fetchall()
    
    # Fetch teacher assignments with teacher names
    cursor.execute("""
        SELECT ta.ID, t.name as teacher_name 
        FROM teacher_assignment ta
        JOIN teacher t ON ta.teacher_id = t.ID
        ORDER BY t.name
    """)
    teacher_assignments = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Insert Grade - Director Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        
    </head>
    <body>
        <div class="container py-4">
            <a href="/director/director_dashboard" class="btn btn-secondary back-link">
                <i class="fas fa-arrow-left"></i> Back to Dashboard
            </a>
            
            <div class="form-container">
                <h2><i class="fas fa-plus-circle"></i> Insert New Grade</h2>
                
                {% if message %}
                    <div class="alert alert-{{ 'success' if message_type == 'success' else 'danger' }}">
                        {{ message }}
                    </div>
                {% endif %}
                
                <form method="POST">
                    <div class="form-group">
                        <label for="level">Grade Level:</label>
                        <input type="text" class="form-control" id="level" name="level" required 
                               placeholder="e.g., Grade 1, Grade 2, KG-1, etc.">
                        <small class="info-text">Enter the grade name (e.g., Grade 1, Grade 2, KG-1)</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="section_id">Select Section:</label>
                        <select class="form-control" id="section_id" name="section_id" required>
                            <option value="">-- Select Section --</option>
                            {% for section in sections %}
                                <option value="{{ section.sec_name }}">Section {{ section.sec_name }}</option>
                            {% endfor %}
                        </select>
                        <small class="info-text">Available sections: A, B, C, D, etc.</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="teacher_assignment_id">Select Teacher:</label>
                        <select class="form-control" id="teacher_assignment_id" name="teacher_assignment_id" required>
                            <option value="">-- Select Teacher --</option>
                            {% for teacher in teacher_assignments %}
                                <option value="{{ teacher.ID }}">{{ teacher.teacher_name }}</option>
                            {% endfor %}
                        </select>
                        <small class="info-text">Select the teacher assigned to this grade</small>
                    </div>
                    
                    <button type="submit" class="btn-submit">
                        <i class="fas fa-save"></i> Insert Grade
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