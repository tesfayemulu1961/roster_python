# ==============================================
# View Room Teachers - Narrow Display with Pagination
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import math

director_view_room_teachers = Blueprint('director_view_room_teachers', __name__, url_prefix='/director')

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

@director_view_room_teachers.route('/view_room_teachers')
@login_required
def view_room_teachers_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    academic_year_id = request.args.get('academic_year', 3, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    offset = (page - 1) * per_page
    
    cursor.execute("SELECT ID, year FROM academic_year ORDER BY year DESC")
    academic_years = cursor.fetchall()
    
    # Get total count for pagination
    count_query = """
        SELECT COUNT(*) as total FROM teacher_assignment ta
        JOIN teacher t ON ta.teacher_id = t.ID
        WHERE ta.is_room_teacher = 1 AND ta.academic_year_id = %s
    """
    cursor.execute(count_query, (academic_year_id,))
    total_count = cursor.fetchone()['total']
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    
    # Main query with pagination
    query = """
        SELECT 
            t.ID, t.name, t.t_id, t.phone, t.email,
            g.level as grade_name,
            s.sec_name as section_name,
            ay.year as academic_year
        FROM teacher_assignment ta
        JOIN teacher t ON ta.teacher_id = t.ID
        JOIN grade g ON ta.grade_id = g.ID
        JOIN section s ON ta.section_id = s.ID
        JOIN academic_year ay ON ta.academic_year_id = ay.ID
        WHERE ta.is_room_teacher = 1
        AND ta.academic_year_id = %s
        ORDER BY g.ID, s.sec_name
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, (academic_year_id, per_page, offset))
    teachers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Room Teachers</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        <style>
            .container-narrow {
                max-width: 1000px;
                margin: 0 auto;
            }
        </style>
    </head>
    <body>
        <div class="container-narrow py-3">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4><i class="fas fa-chalkboard-user"></i> Room Teachers by Section</h4>
                <a href="/director/director_dashboard" class="btn btn-secondary btn-sm">Back to Dashboard</a>
            </div>
            
            <!-- Stats Bar -->
            <div class="alert alert-light d-flex justify-content-between align-items-center mb-3">
                <div>
                    <strong>{{ teachers|length }}</strong> on this page |
                    <strong>{{ total_count }}</strong> total room teachers |
                    <strong>{{ total_pages }}</strong> pages
                </div>
                <div class="d-flex align-items-center gap-2">
                    <span class="text-muted small">Show:</span>
                    <select class="form-select form-select-sm" style="width: auto;" onchange="window.location.href=updateQueryString('per_page', this.value)">
                        <option value="15" {% if per_page == 15 %}selected{% endif %}>15</option>
                        <option value="25" {% if per_page == 25 %}selected{% endif %}>25</option>
                        <option value="50" {% if per_page == 50 %}selected{% endif %}>50</option>
                        <option value="100" {% if per_page == 100 %}selected{% endif %}>100</option>
                    </select>
                </div>
            </div>
            
            <!-- Filter -->
            <div class="card mb-3">
                <div class="card-body">
                    <form method="GET" class="row g-2">
                        <div class="col-md-6">
                            <label class="form-label">Academic Year</label>
                            <select name="academic_year" class="form-select" onchange="this.form.submit()">
                                {% for ay in academic_years %}
                                    <option value="{{ ay.ID }}" {% if academic_year_id == ay.ID %}selected{% endif %}>
                                        {{ ay.year }}
                                    </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">&nbsp;</label>
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-sync-alt"></i> Apply Filter
                            </button>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Teachers Table -->
            {% if teachers %}
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Teacher ID</th>
                            <th>Name</th>
                            <th>Phone</th>
                            <th>Email</th>
                            <th>Grade</th>
                            <th>Section</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for t in teachers %}
                        <tr>
                            <td>{{ t.t_id }}</td>
                            <td>{{ t.name }}</td>
                            <td>{{ t.phone or '—' }}</td>
                            <td>{{ t.email or '—' }}</td>
                            <td>{{ t.grade_name }}</td>
                            <td>{{ t.section_name }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <!-- Pagination -->
            {% if total_pages > 1 %}
            <div class="d-flex justify-content-center gap-2 mt-3">
                {% if page > 1 %}
                    <a href="?page={{ page-1 }}&per_page={{ per_page }}&academic_year={{ academic_year_id }}" 
                       class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-chevron-left"></i> Prev
                    </a>
                {% endif %}
                
                {% set start_page = [page-2, 1]|max %}
                {% set end_page = [page+2, total_pages]|min %}
                
                {% for p in range(start_page, end_page + 1) %}
                    {% if p == page %}
                        <button class="btn btn-sm btn-primary">{{ p }}</button>
                    {% else %}
                        <a href="?page={{ p }}&per_page={{ per_page }}&academic_year={{ academic_year_id }}" 
                           class="btn btn-sm btn-outline-primary">{{ p }}</a>
                    {% endif %}
                {% endfor %}
                
                {% if page < total_pages %}
                    <a href="?page={{ page+1 }}&per_page={{ per_page }}&academic_year={{ academic_year_id }}" 
                       class="btn btn-sm btn-outline-primary">
                        Next <i class="fas fa-chevron-right"></i>
                    </a>
                {% endif %}
            </div>
            {% endif %}
            
            <div class="text-center text-muted mt-2 small">
                Showing {{ teachers|length }} of {{ total_count }} room teachers | Page {{ page }} of {{ total_pages }}
            </div>
            
            {% else %}
            <div class="alert alert-info text-center">
                <i class="fas fa-chalkboard-user fa-2x mb-2 d-block"></i>
                <p class="mb-0">No room teachers found for this academic year</p>
                <small>Try selecting a different academic year</small>
            </div>
            {% endif %}
        </div>
        
        <script>
            function updateQueryString(key, value) {
                const urlParams = new URLSearchParams(window.location.search);
                urlParams.set(key, value);
                urlParams.set('page', 1);
                return window.location.pathname + '?' + urlParams.toString();
            }
        </script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    teachers=teachers, 
    academic_years=academic_years, 
    academic_year_id=academic_year_id,
    page=page,
    total_pages=total_pages,
    per_page=per_page,
    total_count=total_count
    )