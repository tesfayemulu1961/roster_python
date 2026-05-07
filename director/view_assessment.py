# ==============================================
# view_transfer_sheet.py - Fixed column names
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import math

director_view_transfer_sheet = Blueprint('director_view_transfer_sheet', __name__, url_prefix='/director')

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

@director_view_transfer_sheet.route('/view_transfer_sheet')
@login_required
def view_transfer_sheet_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    offset = (page - 1) * per_page
    search = request.args.get('search', '', type=str)
    
    where_clause = "1=1"
    params = []
    
    if search:
        where_clause += " AND (s.name LIKE %s OR s.studid LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param])
    
    # Total count query (fixed join)
    count_query = f"""
        SELECT COUNT(*) as total
        FROM transfer_sheet ts
        JOIN student s ON ts.student_RN = s.RN
        WHERE {where_clause}
    """
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()['total']
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    
    # Main query with corrected joins and narrower container
    query = f"""
        SELECT 
            ts.*,
            s.name as student_name,
            s.studid as student_code,
            g.level as from_grade,
            sec1.sec_name as from_section,
            g2.level as to_grade,
            sec2.sec_name as to_section
        FROM transfer_sheet ts
        JOIN student s ON ts.student_RN = s.RN
        JOIN grade g ON ts.from_grade_id = g.ID
        JOIN section sec1 ON ts.from_section_id = sec1.ID
        JOIN grade g2 ON ts.to_grade_id = g2.ID
        JOIN section sec2 ON ts.to_section_id = sec2.ID
        WHERE {where_clause}
        ORDER BY ts.transfer_date DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, params + [per_page, offset])
    transfers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Transfer Sheet</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        <style>
            .container-narrow { max-width: 1000px; margin: 0 auto; }
        </style>
    </head>
    <body>
        <div class="container-narrow py-3">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4><i class="fas fa-exchange-alt"></i> Student Transfer Sheet</h4>
                <a href="/director/director_dashboard" class="btn btn-secondary btn-sm">Back to Dashboard</a>
            </div>
            
            <div class="card mb-3">
                <div class="card-body">
                    <form method="GET" class="row g-2">
                        <div class="col-md-8">
                            <input type="text" name="search" class="form-control" placeholder="Search by student name or code..." value="{{ search }}">
                        </div>
                        <div class="col-md-2">
                            <select name="per_page" class="form-select" onchange="this.form.submit()">
                                <option value="15" {% if per_page == 15 %}selected{% endif %}>15 per page</option>
                                <option value="25" {% if per_page == 25 %}selected{% endif %}>25 per page</option>
                                <option value="50" {% if per_page == 50 %}selected{% endif %}>50 per page</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <button type="submit" class="btn btn-primary w-100">Filter</button>
                        </div>
                    </form>
                </div>
            </div>
            
            <div class="alert alert-light d-flex justify-content-between mb-3">
                <div>
                    <strong>{{ transfers|length }}</strong> on this page |
                    <strong>{{ total_count }}</strong> total transfers |
                    <strong>{{ total_pages }}</strong> pages
                </div>
            </div>
            
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Student Code</th>
                            <th>Student Name</th>
                            <th>From</th>
                            <th>To</th>
                            <th>Transfer Date</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for t in transfers %}
                        <tr>
                            <td>{{ t.student_code }}</td>
                            <td>{{ t.student_name }}</td>
                            <td>{{ t.from_grade }} - {{ t.from_section }}</td>
                            <td>{{ t.to_grade }} - {{ t.to_section }}</td>
                            <td>{{ t.transfer_date }}</td>
                            <td>{{ t.reason or '—' }}</td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="6" class="text-center">No transfer records found</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            {% if total_pages > 1 %}
            <div class="d-flex justify-content-center gap-2 mt-3">
                {% if page > 1 %}
                    <a href="?page={{ page-1 }}&per_page={{ per_page }}&search={{ search }}" class="btn btn-sm btn-outline-primary">« Prev</a>
                {% endif %}
                
                {% set start_page = [page-2, 1]|max %}
                {% set end_page = [page+2, total_pages]|min %}
                
                {% for p in range(start_page, end_page + 1) %}
                    {% if p == page %}
                        <button class="btn btn-sm btn-primary">{{ p }}</button>
                    {% else %}
                        <a href="?page={{ p }}&per_page={{ per_page }}&search={{ search }}" class="btn btn-sm btn-outline-primary">{{ p }}</a>
                    {% endif %}
                {% endfor %}
                
                {% if page < total_pages %}
                    <a href="?page={{ page+1 }}&per_page={{ per_page }}&search={{ search }}" class="btn btn-sm btn-outline-primary">Next »</a>
                {% endif %}
            </div>
            {% endif %}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    transfers=transfers,
    page=page,
    total_pages=total_pages,
    per_page=per_page,
    total_count=total_count,
    search=search
    )