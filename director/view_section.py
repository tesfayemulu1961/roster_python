# ==============================================
# View Section - Complete Python Conversion
# Converted from view_section.php
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector

director_view_section = Blueprint('director_view_section', __name__, url_prefix='/director')

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

@director_view_section.route('/view_section')
@login_required
def view_section_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    message = None
    message_type = None
    
    # Handle delete request
    if request.args.get('delete_id'):
        delete_id = request.args.get('delete_id')
        try:
            # Check if section has students
            cursor.execute("SELECT COUNT(*) as count FROM student WHERE section_id = %s", (delete_id,))
            student_count = cursor.fetchone()['count']
            
            if student_count > 0:
                message = f"Cannot delete section because it has {student_count} student(s) assigned."
                message_type = "danger"
            else:
                cursor.execute("DELETE FROM section WHERE ID = %s", (delete_id,))
                conn.commit()
                message = "Section deleted successfully!"
                message_type = "success"
        except Exception as e:
            message = f"Error deleting section: {e}"
            message_type = "danger"
    
    # Fetch all sections with grade information
    cursor.execute("""
        SELECT 
            s.ID,
            s.sec_name,
            g.ID as grade_id,
            g.level as grade_level,
            (SELECT COUNT(*) FROM student WHERE section_id = s.ID) as student_count
        FROM section s
        LEFT JOIN grade g ON s.grade_id = g.ID
        ORDER BY g.ID, s.sec_name
    """)
    sections = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>View Sections - Director Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        
    </head>
    <body>
        <div class="container py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="fas fa-door-open"></i> View Sections</h2>
                <div>
                    <a href="/director/insert_section" class="btn btn-primary">
                        <i class="fas fa-plus"></i> Add New Section
                    </a>
                    <a href="/director/director_dashboard" class="btn btn-secondary">
                        <i class="fas fa-arrow-left"></i> Back to Dashboard
                    </a>
                </div>
            </div>
            
            {% if message %}
                <div class="alert alert-{{ message_type }} alert-dismissible fade show">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endif %}
            
            <!-- Group sections by grade -->
            {% set grades = {} %}
            {% for section in sections %}
                {% set grade_key = section.grade_id %}
                {% if grade_key not in grades %}
                    {% set _ = grades.update({grade_key: {'grade_level': section.grade_level, 'sections': []}}) %}
                {% endif %}
                {% set _ = grades[grade_key]['sections'].append(section) %}
            {% endfor %}
            
            <div class="row">
                {% for grade_id, grade_data in grades.items() %}
                <div class="col-md-6 mb-4">
                    <div class="section-card">
                        <div class="grade-header">
                            <h4 class="mb-0">{{ grade_data.grade_level }}</h4>
                            <small>{{ grade_data.sections|length }} Sections</small>
                        </div>
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead class="table-light">
                                    <tr>
                                        <th>Section Name</th>
                                        <th>Students Count</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for section in grade_data.sections %}
                                    <tr>
                                        <td><span class="badge bg-primary fs-6">{{ section.sec_name }}</span></td>
                                        <td><span class="badge bg-info">{{ section.student_count }}</span> students</td>
                                        <td>
                                            <div class="btn-group" role="group">
                                                <a href="/director/edit_section?edit_id={{ section.ID }}" class="btn btn-warning btn-sm">
                                                    <i class="fas fa-edit"></i>
                                                </a>
                                                <button type="button" class="btn btn-danger btn-sm" data-bs-toggle="modal" data-bs-target="#deleteModal{{ section.ID }}">
                                                    <i class="fas fa-trash"></i>
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                    
                                    <!-- Delete Modal -->
                                    <div class="modal fade" id="deleteModal{{ section.ID }}" tabindex="-1">
                                        <div class="modal-dialog">
                                            <div class="modal-content">
                                                <div class="modal-header">
                                                    <h5 class="modal-title">Confirm Delete</h5>
                                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                                </div>
                                                <div class="modal-body">
                                                    <p>Are you sure you want to delete section <strong>{{ section.sec_name }}</strong>?</p>
                                                    {% if section.student_count > 0 %}
                                                        <p class="text-danger">⚠️ This section has {{ section.student_count }} student(s) assigned!</p>
                                                    {% endif %}
                                                </div>
                                                <div class="modal-footer">
                                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                                    <a href="/director/view_section?delete_id={{ section.ID }}" class="btn btn-danger">Delete</a>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    {% else %}
                                    <tr><td colspan="3" class="text-center">No sections found</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            {% if not grades %}
                <div class="alert alert-info text-center">
                    <i class="fas fa-info-circle"></i> No sections found. 
                    <a href="/director/insert_section">Click here to add your first section.</a>
                </div>
            {% endif %}
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    sections=sections
    )