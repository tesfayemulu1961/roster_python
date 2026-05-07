# ==============================================
# View Subject - With Pagination
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import math

director_view_subject = Blueprint('director_view_subject', __name__, url_prefix='/director')

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

@director_view_subject.route('/view_subject')
@login_required
def view_subject_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    message = None
    message_type = None
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # First, check what columns the subject table has
    cursor.execute("SHOW COLUMNS FROM subject")
    subject_columns = [col['Field'] for col in cursor.fetchall()]
    
    # Determine the name column
    name_column = None
    for col in ['subject_name', 'name', 'description', 'subject', 'title']:
        if col in subject_columns:
            name_column = col
            break
    
    # Determine the ID column
    id_column = None
    for col in ['ID', 'id', 'subject_id']:
        if col in subject_columns:
            id_column = col
            break
    
    if not id_column and subject_columns:
        id_column = subject_columns[0]
    
    if not name_column:
        name_column = subject_columns[1] if len(subject_columns) > 1 else subject_columns[0]
    
    # Handle delete request
    if request.args.get('delete_id'):
        delete_id = request.args.get('delete_id')
        try:
            cursor.execute(f"DELETE FROM subject WHERE {id_column} = %s", (delete_id,))
            conn.commit()
            message = "Subject deleted successfully!"
            message_type = "success"
            # Redirect to refresh the page
            return redirect(f"/director/view_subject?page={page}&per_page={per_page}")
        except Exception as e:
            message = f"Error deleting subject: {e}"
            message_type = "danger"
    
    # Build the search condition
    search_condition = ""
    search_params = []
    if search:
        search_condition = f" WHERE {name_column} LIKE %s"
        search_params.append(f"%{search}%")
    
    # Get total count for pagination
    count_query = f"SELECT COUNT(*) as total FROM subject{search_condition}"
    cursor.execute(count_query, search_params)
    total_count = cursor.fetchone()['total']
    
    # Calculate total pages
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    
    # Fetch subjects with pagination
    try:
        query = f"""
            SELECT 
                s.{id_column} as id,
                s.{name_column} as subject_name
            FROM subject s
            {search_condition}
            ORDER BY s.{name_column}
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, search_params + [per_page, offset])
        subjects = cursor.fetchall()
    except Exception as e:
        subjects = []
        message = f"Query error: {e}"
        message_type = "danger"
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>View Subjects - Director Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        
    </head>
    <body>
        <div class="container py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="fas fa-book"></i> View Subjects</h2>
                <div>
                    <a href="/director/insert_subject" class="btn btn-primary">
                        <i class="fas fa-plus"></i> Add New Subject
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
                <!-- Search and Filter Bar -->
                <div class="row mb-3 align-items-center">
                    <div class="col-md-6">
                        <form method="GET" class="search-box">
                            <div class="input-group">
                                <input type="text" name="search" class="form-control" 
                                       placeholder="Search subjects..." value="{{ search }}">
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-search"></i> Search
                                </button>
                                {% if search %}
                                    <a href="/director/view_subject" class="btn btn-secondary">
                                        <i class="fas fa-times"></i> Clear
                                    </a>
                                {% endif %}
                            </div>
                        </form>
                    </div>
                    <div class="col-md-6 text-end">
                        <div class="per-page-selector">
                            <label class="me-2">Show:</label>
                            <select class="form-select d-inline-block w-auto" onchange="window.location.href=this.value">
                                <option value="/director/view_subject?page=1&per_page=10&search={{ search }}" 
                                        {% if per_page == 10 %}selected{% endif %}>10</option>
                                <option value="/director/view_subject?page=1&per_page=25&search={{ search }}" 
                                        {% if per_page == 25 %}selected{% endif %}>25</option>
                                <option value="/director/view_subject?page=1&per_page=50&search={{ search }}" 
                                        {% if per_page == 50 %}selected{% endif %}>50</option>
                                <option value="/director/view_subject?page=1&per_page=100&search={{ search }}" 
                                        {% if per_page == 100 %}selected{% endif %}>100</option>
                            </select>
                            <span class="ms-2">entries per page</span>
                        </div>
                    </div>
                </div>
                
                <!-- Subjects Table -->
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th>ID</th>
                                <th>Subject Name</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for subject in subjects %}
                            <tr>
                                <td>{{ subject.id }}</td>
                                <td>{{ subject.subject_name }}</td>
                                <td>
                                    <div class="btn-group" role="group">
                                        <a href="/director/edit_subject?edit_id={{ subject.id }}" class="btn btn-warning btn-sm">
                                            <i class="fas fa-edit"></i> Edit
                                        </a>
                                        <button type="button" class="btn btn-danger btn-sm" data-bs-toggle="modal" data-bs-target="#deleteModal{{ subject.id }}">
                                            <i class="fas fa-trash"></i> Delete
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Delete Modal -->
                            <div class="modal fade" id="deleteModal{{ subject.id }}" tabindex="-1">
                                <div class="modal-dialog">
                                    <div class="modal-content">
                                        <div class="modal-header">
                                            <h5 class="modal-title">Confirm Delete</h5>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                        </div>
                                        <div class="modal-body">
                                            <p>Are you sure you want to delete subject <strong>{{ subject.subject_name }}</strong>?</p>
                                            <p class="text-danger">This action cannot be undone!</p>
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                            <a href="/director/view_subject?delete_id={{ subject.id }}&page={{ page }}&per_page={{ per_page }}&search={{ search }}" 
                                               class="btn btn-danger">Delete</a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {% else %}
                            <tr>
                                <td colspan="3" class="text-center">
                                    {% if search %}
                                        No subjects found matching "{{ search }}". 
                                        <a href="/director/view_subject">Clear search</a>
                                    {% else %}
                                        No subjects found. <a href="/director/insert_subject">Add your first subject</a>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                
                <!-- Pagination -->
                {% if total_pages > 1 %}
                <div class="pagination-container">
                    <ul class="pagination">
                        <!-- First Page -->
                        {% if page > 1 %}
                        <li>
                            <a href="/director/view_subject?page=1&per_page={{ per_page }}&search={{ search }}">
                                <i class="fas fa-angle-double-left"></i>
                            </a>
                        </li>
                        {% else %}
                        <li class="disabled">
                            <span><i class="fas fa-angle-double-left"></i></span>
                        </li>
                        {% endif %}
                        
                        <!-- Previous Page -->
                        {% if page > 1 %}
                        <li>
                            <a href="/director/view_subject?page={{ page-1 }}&per_page={{ per_page }}&search={{ search }}">
                                <i class="fas fa-angle-left"></i>
                            </a>
                        </li>
                        {% else %}
                        <li class="disabled">
                            <span><i class="fas fa-angle-left"></i></span>
                        </li>
                        {% endif %}
                        
                        <!-- Page Numbers -->
                        {% set start_page = [page-2, 1]|max %}
                        {% set end_page = [page+2, total_pages]|min %}
                        
                        {% if start_page > 1 %}
                        <li class="disabled"><span>...</span></li>
                        {% endif %}
                        
                        {% for p in range(start_page, end_page + 1) %}
                            {% if p == page %}
                            <li class="active">
                                <span>{{ p }}</span>
                            </li>
                            {% else %}
                            <li>
                                <a href="/director/view_subject?page={{ p }}&per_page={{ per_page }}&search={{ search }}">
                                    {{ p }}
                                </a>
                            </li>
                            {% endif %}
                        {% endfor %}
                        
                        {% if end_page < total_pages %}
                        <li class="disabled"><span>...</span></li>
                        {% endif %}
                        
                        <!-- Next Page -->
                        {% if page < total_pages %}
                        <li>
                            <a href="/director/view_subject?page={{ page+1 }}&per_page={{ per_page }}&search={{ search }}">
                                <i class="fas fa-angle-right"></i>
                            </a>
                        </li>
                        {% else %}
                        <li class="disabled">
                            <span><i class="fas fa-angle-right"></i></span>
                        </li>
                        {% endif %}
                        
                        <!-- Last Page -->
                        {% if page < total_pages %}
                        <li>
                            <a href="/director/view_subject?page={{ total_pages }}&per_page={{ per_page }}&search={{ search }}">
                                <i class="fas fa-angle-double-right"></i>
                            </a>
                        </li>
                        {% else %}
                        <li class="disabled">
                            <span><i class="fas fa-angle-double-right"></i></span>
                        </li>
                        {% endif %}
                    </ul>
                </div>
                
                <!-- Entries Info -->
                <div class="entries-info">
                    Showing {{ ((page-1) * per_page) + 1 }} to 
                    {{ [page * per_page, total_count]|min }} of 
                    {{ total_count }} entries
                </div>
                {% endif %}
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    subjects=subjects,
    message=message,
    message_type=message_type,
    page=page,
    per_page=per_page,
    total_pages=total_pages,
    total_count=total_count,
    search=search
    )