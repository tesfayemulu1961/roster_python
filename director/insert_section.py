# ==============================================
# Insert Section - Complete Python Conversion
# Converted from insert_section.php
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector

director_insert_section = Blueprint('director_insert_section', __name__, url_prefix='/director')

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

@director_insert_section.route('/insert_section', methods=['GET', 'POST'])
@login_required
def insert_section_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    message = None
    message_type = None
    
    # Fetch grades for dropdown
    cursor.execute("SELECT ID, level FROM grade ORDER BY ID")
    grades = cursor.fetchall()
    
    if request.method == 'POST':
        sec_name = request.form.get('sec_name', '').strip()
        grade_id = request.form.get('grade_id', '')
        
        if not sec_name or not grade_id:
            message = "Error: Please fill all required fields"
            message_type = "danger"
        else:
            try:
                cursor.execute("""
                    INSERT INTO section (sec_name, grade_id) 
                    VALUES (%s, %s)
                """, (sec_name, grade_id))
                conn.commit()
                message = f"Section {sec_name} added successfully!"
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
        <title>Insert Section - Director Dashboard</title>
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
                <h2><i class="fas fa-plus-circle"></i> Insert New Section</h2>
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
                        <label for="sec_name" class="form-label">Section Name <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" id="sec_name" name="sec_name" required 
                               placeholder="e.g., A, B, C, D, E">
                        <small class="text-muted">Enter section letter (A, B, C, D, E, etc.)</small>
                    </div>
                    
                    <div class="mb-3">
                        <label for="grade_id" class="form-label">Select Grade <span class="text-danger">*</span></label>
                        <select class="form-control" id="grade_id" name="grade_id" required>
                            <option value="">-- Select Grade --</option>
                            {% for grade in grades %}
                                <option value="{{ grade.ID }}">{{ grade.level }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="fas fa-save"></i> Insert Section
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
    message=message,
    message_type=message_type
    )