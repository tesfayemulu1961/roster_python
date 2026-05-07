# ==============================================
# View Subject Teachers - Narrow Display with Pagination
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import math

director_view_subject_teachers = Blueprint('director_view_subject_teachers', __name__, url_prefix='/director')

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

@director_view_subject_teachers.route('/view_subject_teachers')
@login_required
def view_subject_teachers_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    academic_year_id = request.args.get('academic_year', 3, type=int)
    grade_filter = request.args.get('grade_filter', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    offset = (page - 1) * per_page
    
    cursor.execute("SELECT ID, year FROM academic_year ORDER BY year DESC")
    academic_years = cursor.fetchall()
    
    cursor.execute("SELECT ID, level FROM grade ORDER BY ID")
    grades = cursor.fetchall()
    
    # Build WHERE clause
    where_clause = "ta.is_subject_teacher = 1 AND ta.academic_year_id = %s"
    params = [academic_year_id]
    
    if grade_filter:
        where_clause += " AND g.level = %s"
        params.append(grade_filter)
    
    # Get total count for pagination
    count_query = f"""
        SELECT COUNT(*) as total 
        FROM teacher_assignment ta
        JOIN teacher t ON ta.teacher_id = t.ID
        JOIN grade g ON ta.grade_id = g.ID
        JOIN subject sub ON ta.subject_id = sub.id
        WHERE {where_clause}
    """
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()['total']
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    
    # Main query with pagination
    query = f"""
        SELECT 
            t.ID, t.name, t.t_id, t.phone, t.email,
            g.level as grade_name,
            sub.sub_name as subject_name,
            ay.year as academic_year
        FROM teacher_assignment ta
        JOIN teacher t ON ta.teacher_id = t.ID
        JOIN grade g ON ta.grade_id = g.ID
        JOIN subject sub ON ta.subject_id = sub.id
        JOIN academic_year ay ON ta.academic_year_id = ay.ID
        WHERE {where_clause}
        ORDER BY g.ID, sub.sub_name
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, params + [per_page, offset])
    teachers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Subject Teachers</title>
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
            <div class="d-flex justify-content-between mb-3">
                <h4><i class="fas fa-book-open"></i> Subject Teachers by Subject</h4>
                <a href="/director/director_dashboard" class="btn btn-secondary btn-sm">Back</a>
            </div>
            
            <div class="card mb-3">
                <div class="card-body">
                    <form method="GET" class="row g-2">
                        <div class="col-md-4">
                            <label>Academic Year</label>
                            <select name="academic_year" class="form-select" onchange="this.form.submit()">
                                {% for ay in academic_years %}
                                    <option value="{{ ay.ID }}" {% if academic_year_id == ay.ID %}selected{% endif %}>
                                        {{ ay.year }}
                                    </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label>Grade</label>
                            <select name="grade_filter" class="form-select" onchange="this.form.submit()">
                                <option value="">All Grades</option>
                                {% for g in grades %}
                                    <option value="{{ g.level }}" {% if grade_filter == g.level %}selected{% endif %}>
                                        {{ g.level }}
                                    </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label>&nbsp;</label>
                            <select name="per_page" class="form-select" onchange="this.form.submit()">
                                <option value="15" {% if per_page == 15 %}selected{% endif %}>15 per page</option>
                                <option value="25" {% if per_page == 25 %}selected{% endif %}>25 per page</option>
                                <option value="50" {% if per_page == 50 %}selected{% endif %}>50 per page</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label>&nbsp;</label>
                            <button type="submit" class="btn btn-primary w-100">Filter</button>
                        </div>
                    </form>
                </div>
            </div>
            
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Teacher ID</th>
                            <th>Name</th>
                            <th>Phone</th>
                            <th>Email</th>
                            <th>Grade</th>
                            <th>Subject</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for t in teachers %}
                        <tr>
                            <td>{{ t.t_id }}</td>
                            <td>{{ t.name }}</td>
                            <td>{{ t.phone or 'N/A' }}</td>
                            <td>{{ t.email or 'N/A' }}</td>
                            <td>{{ t.grade_name }}</td>
                            <td>{{ t.subject_name }}</td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="6" class="text-center">No subject teachers found</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            {% if total_pages > 1 %}
            <div class="pagination justify-content-center mt-3">
                {% if page > 1 %}
                    <a href="?page={{ page-1 }}&per_page={{ per_page }}&academic_year={{ academic_year_id }}&grade_filter={{ grade_filter }}" 
                       class="btn btn-sm btn-outline-primary">« Prev</a>
                {% endif %}
                
                {% for p in range(1, total_pages + 1) %}
                    {% if p == page %}
                        <button class="btn btn-sm btn-primary">{{ p }}</button>
                    {% else %}
                        <a href="?page={{ p }}&per_page={{ per_page }}&academic_year={{ academic_year_id }}&grade_filter={{ grade_filter }}" 
                           class="btn btn-sm btn-outline-primary">{{ p }}</a>
                    {% endif %}
                {% endfor %}
                
                {% if page < total_pages %}
                    <a href="?page={{ page+1 }}&per_page={{ per_page }}&academic_year={{ academic_year_id }}&grade_filter={{ grade_filter }}" 
                       class="btn btn-sm btn-outline-primary">Next »</a>
                {% endif %}
            </div>
            {% endif %}
            
            <div class="text-center text-muted mt-2 small">
                Showing {{ teachers|length }} of {{ total_count }} subject teachers | Page {{ page }} of {{ total_pages }}
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    teachers=teachers, 
    academic_years=academic_years, 
    academic_year_id=academic_year_id,
    grades=grades, 
    grade_filter=grade_filter,
    page=page,
    total_pages=total_pages,
    per_page=per_page,
    total_count=total_count
    )