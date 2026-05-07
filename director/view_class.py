# ==============================================
# View Class - Simple Working Version
# ==============================================

from flask import Blueprint, render_template_string, session, redirect
from functools import wraps
import mysql.connector

director_view_class = Blueprint('director_view_class', __name__, url_prefix='/director')

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

@director_view_class.route('/view_class')
@login_required
def view_class_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Try a simple query first
        cursor.execute("SELECT * FROM class")
        classes = cursor.fetchall()
    except Exception as e:
        # If error, show the error message
        classes = []
        error_msg = str(e)
    finally:
        cursor.close()
        conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>View Classes - Director Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
    </head>
    <body>
        <div class="container py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="fas fa-school"></i> View Classes</h2>
                <a href="/director/director_dashboard" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i> Back to Dashboard
                </a>
            </div>
            
            {% if error_msg %}
                <div class="alert alert-danger">
                    <strong>Database Error:</strong> {{ error_msg }}
                    <hr>
                    <p>Please check that the 'class' table exists in your database.</p>
                </div>
            {% endif %}
            
            <div class="card">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead class="table-dark">
                                <tr>
                                    {% if classes %}
                                        {% for key in classes[0].keys() %}
                                            <th>{{ key }}</th>
                                        {% endfor %}
                                        <th>Actions</th>
                                    {% else %}
                                        <th>No Data</th>
                                    {% endif %}
                                </tr>
                            </thead>
                            <tbody>
                                {% for class_item in classes %}
                                <tr>
                                    {% for value in class_item.values() %}
                                        <td>{{ value }}</td>
                                    {% endfor %}
                                    <td>
                                        <button class="btn btn-warning btn-sm" disabled>Edit</button>
                                        <button class="btn btn-danger btn-sm" disabled>Delete</button>
                                    </td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="10" class="text-center">No classes found in the database.</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    classes=classes,
    error_msg=error_msg if 'error_msg' in locals() else None
    )