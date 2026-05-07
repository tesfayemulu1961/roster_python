# ==============================================
# View Grade - Complete Python Conversion (Fixed)
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector

director_view_grade = Blueprint('director_view_grade', __name__, url_prefix='/director')

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

@director_view_grade.route('/view_grade')
@login_required
def view_grade_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    message = None
    message_type = None
    
    # Handle delete request
    if request.args.get('delete_id'):
        delete_id = request.args.get('delete_id')
        try:
            cursor.execute("DELETE FROM grade WHERE ID = %s", (delete_id,))
            conn.commit()
            message = "Grade deleted successfully!"
            message_type = "success"
        except Exception as e:
            message = f"Error deleting grade: {e}"
            message_type = "danger"
    
    # Fetch all grades - Fixed query without section_id
    cursor.execute("""
        SELECT 
            g.ID,
            g.level,
            g.teacher_assignment_id,
            t.name as teacher_name,
            t.phone as teacher_phone
        FROM grade g
        LEFT JOIN teacher_assignment ta ON g.teacher_assignment_id = ta.ID
        LEFT JOIN teacher t ON ta.teacher_id = t.ID
        ORDER BY g.ID
    """)
    grades = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>View Grades - Director Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        <style>
            .table-container {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
        </style>
    </head>
    <body>
        <div class="container py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="fas fa-eye"></i> View Grades</h2>
                <div>
                    <a href="/director/insert_grade" class="btn btn-primary">
                        <i class="fas fa-plus"></i> Add New Grade
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
            
            <div class="table-container">
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th>ID</th>
                                <th>Grade Level</th>
                                <th>Teacher Name</th>
                                <th>Teacher Phone</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for grade in grades %}
                            <tr>
                                <td>{{ grade.ID }}             </td>
                                <td>{{ grade.level or 'N/A' }}  </td>
                                <td>{{ grade.teacher_name or 'Not Assigned' }}</td>
                                <td>{{ grade.teacher_phone or 'N/A' }}      </td>
                                <td>
                                    <div class="btn-group" role="group">
                                        <a href="/director/edit_grade?edit_id={{ grade.ID }}" class="btn btn-warning btn-sm">
                                            <i class="fas fa-edit"></i> Edit
                                        </a>
                                        <button type="button" class="btn btn-danger btn-sm" data-bs-toggle="modal" data-bs-target="#deleteModal{{ grade.ID }}">
                                            <i class="fas fa-trash"></i> Delete
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Delete Confirmation Modal -->
                            <div class="modal fade" id="deleteModal{{ grade.ID }}" tabindex="-1">
                                <div class="modal-dialog">
                                    <div class="modal-content">
                                        <div class="modal-header">
                                            <h5 class="modal-title">Confirm Delete</h5>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                        </div>
                                        <div class="modal-body">
                                            <p>Are you sure you want to delete grade <strong>{{ grade.level }}</strong>?</p>
                                            <p class="text-danger">This action cannot be undone!</p>
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                            <a href="/director/view_grade?delete_id={{ grade.ID }}" class="btn btn-danger">Delete</a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {% else %}
                            <tr>
                                <td colspan="5" class="text-center">No grades found. <a href="/director/insert_grade">Add your first grade</a></td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
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