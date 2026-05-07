# ==============================================
# View Student & Parent Records - Complete Python Conversion
# Converted from view_student_parent_paginated.php
# NO INNER CSS/JS - All external
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector

view_student_parent_bp = Blueprint('view_student_parent', __name__, url_prefix='/director')

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

@view_student_parent_bp.route('/view_student_parent_paginated')
@login_required
def view_student_parent_paginated():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get parameters
    selected_academic_year = request.args.get('academic_year', 2, type=int)
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    per_page = 10
    
    # Get all academic years for dropdown
    cursor.execute("SELECT ID, year FROM academic_year ORDER BY year DESC")
    academic_years = cursor.fetchall()
    
    # Get academic year name for display
    cursor.execute("SELECT year FROM academic_year WHERE ID = %s", (selected_academic_year,))
    year_result = cursor.fetchone()
    academic_year_name = year_result['year'] if year_result else "Selected"
    
    # Pagination calculation
    start = (page - 1) * per_page
    
    # Reset row number variable
    cursor.execute("SET @row_number = 0")
    
    # Build the query
    sql = """
        SELECT SQL_CALC_FOUND_ROWS 
        (@row_number:=@row_number + 1) AS auto_number,
        s.RN as student_RN, 
        s.fullname,
        s.gender,
        s.parent_id,
        p.ID as parent_db_id,
        p.p_id,
        p.p_name,
        p.phone,
        p.email,
        e.studid,
        g.level AS grade_name, 
        sec.sec_name AS section_name, 
        t.name AS teacher_name, 
        ay.year AS academic_year_date
        FROM student s
        LEFT JOIN parent p ON s.parent_id = p.ID
        LEFT JOIN enrollment e ON s.RN = e.student_RN
        LEFT JOIN grade g ON s.grade_id = g.ID
        LEFT JOIN section sec ON s.section_id = sec.ID
        LEFT JOIN teacher t ON s.teacher_id = t.ID
        LEFT JOIN academic_year ay ON s.academic_year_id = ay.ID
        WHERE s.academic_year_id = %s
    """
    params = [selected_academic_year]
    
    # Add search condition
    if search:
        search_term = f"%{search}%"
        sql += """ AND (e.studid LIKE %s 
                  OR s.fullname LIKE %s
                  OR p.p_name LIKE %s
                  OR p.p_id LIKE %s)"""
        params.extend([search_term, search_term, search_term, search_term])
    
    # Group by RN to remove duplicates and add pagination
    sql += " GROUP BY s.RN ORDER BY s.RN ASC LIMIT %s OFFSET %s"
    params.extend([per_page, start])
    
    cursor.execute(sql, params)
    records = cursor.fetchall()
    
    # Get total records for pagination
    cursor.execute("SELECT FOUND_ROWS() as total")
    total_results = cursor.fetchone()['total']
    total_pages = (total_results + per_page - 1) // per_page
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Student & Parent Records - {{ academic_year_name }}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
        <link rel="stylesheet" href="/static/css/core.css">
        <link rel="stylesheet" href="/static/css/student_parent_records.css">
    </head>
    <body>
        <div class="container">
            {% if request.args.get('delete_success') %}
                <div class="alert-success">Record deleted successfully</div>
            {% endif %}
            {% if request.args.get('delete_error') %}
                <div class="alert-danger">{{ request.args.get('delete_error') }}</div>
            {% endif %}
            
            <div class="header">
                <h1>Student & Parent Records - {{ academic_year_name }}</h1>
                <p>Showing unique records based on Roll Number (RN)</p>
            </div>

            <!-- Search and Filter Box -->
            <div class="search-container">
                <form method="get" class="search-form">
                    <input type="text" name="search" class="search-input" 
                           placeholder="Search by student ID, name, or parent details..." 
                           value="{{ search }}">
                    
                    <select name="academic_year" class="academic-year-select">
                        {% for year in academic_years %}
                            <option value="{{ year.ID }}" {% if selected_academic_year == year.ID %}selected{% endif %}>
                                {{ year.year }}
                            </option>
                        {% endfor %}
                    </select>
                    
                    <button type="submit" class="btn search-btn">Search</button>
                    
                    {% if search or selected_academic_year != 2 %}
                        <a href="/director/view_student_parent_paginated" class="btn reset-btn">Reset to Default</a>
                    {% endif %}
                </form>
            </div>

            <div class="actions">
                <a href="/director/insert_student_parent" class="btn btn-back">Back to Registration</a>
                <div class="current-year-badge">
                    Current View: {{ academic_year_name }}
                </div>
            </div>

            {% if records %}
                <table class="data-table" id="recordsTable">
                    <thead>
                        <tr>
                            <th>No.</th>
                            <th>Roll No</th>
                            <th>Student Name</th>
                            <th>Grade</th>
                            <th>Section</th>
                            <th>Parent Name</th>
                            <th>Parent ID</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in records %}
                        <tr>
                            <td>{{ row.auto_number }}</td>
                            <td>{{ row.student_RN }}</td>
                            <td>{{ row.fullname }}</td>
                            <td>{{ row.grade_name or 'N/A' }}</td>
                            <td>{{ row.section_name or 'N/A' }}</td>
                            <td>{{ row.p_name or 'N/A' }}</td>
                            <td>{{ row.p_id or 'N/A' }}</td>
                            <td>
                                <a href="/director/view_student_parent?search={{ row.studid }}" class="btn-view">View</a>
                                <a href="/director/edit_student_parent?id={{ row.student_RN }}" class="btn-edit">Edit</a>
                                <a href="/director/delete_record_student_parent?type=student&id={{ row.student_RN }}" 
                                   class="btn-delete" 
                                   onclick="return confirm('Are you sure you want to delete this record?')">Delete</a>
                             </td>
                         </tr>
                        {% endfor %}
                    </tbody>
                </table>

                <div class="record-count">
                    Showing {{ start + 1 }} to {{ [start + per_page, total_results]|min }} of {{ "{:,}".format(total_results) }} records
                </div>

                <!-- Pagination -->
                <ul class="pagination">
                    {% if page > 1 %}
                        <li><a href="?page={{ page-1 }}&academic_year={{ selected_academic_year }}{% if search %}&search={{ search }}{% endif %}">Previous</a></li>
                    {% else %}
                        <li class="disabled"><span>Previous</span></li>
                    {% endif %}

                    {% set max_visible_pages = 5 %}
                    {% set half = max_visible_pages // 2 %}
                    {% set start_page = [1, page - half]|max %}
                    {% set end_page = [total_pages, start_page + max_visible_pages - 1]|min %}
                    
                    {% if end_page - start_page + 1 < max_visible_pages %}
                        {% set start_page = [1, end_page - max_visible_pages + 1]|max %}
                    {% endif %}
                    
                    {% if start_page > 1 %}
                        <li><a href="?page=1&academic_year={{ selected_academic_year }}{% if search %}&search={{ search }}{% endif %}">1</a></li>
                        {% if start_page > 2 %}
                            <li class="disabled"><span>...</span></li>
                        {% endif %}
                    {% endif %}
                    
                    {% for i in range(start_page, end_page + 1) %}
                        {% if i == page %}
                            <li class="active"><span>{{ i }}</span></li>
                        {% else %}
                            <li><a href="?page={{ i }}&academic_year={{ selected_academic_year }}{% if search %}&search={{ search }}{% endif %}">{{ i }}</a></li>
                        {% endif %}
                    {% endfor %}
                    
                    {% if end_page < total_pages %}
                        {% if end_page < total_pages - 1 %}
                            <li class="disabled"><span>...</span></li>
                        {% endif %}
                        <li><a href="?page={{ total_pages }}&academic_year={{ selected_academic_year }}{% if search %}&search={{ search }}{% endif %}">{{ total_pages }}</a></li>
                    {% endif %}

                    {% if page < total_pages %}
                        <li><a href="?page={{ page+1 }}&academic_year={{ selected_academic_year }}{% if search %}&search={{ search }}{% endif %}">Next</a></li>
                    {% else %}
                        <li class="disabled"><span>Next</span></li>
                    {% endif %}
                </ul>
            {% else %}
                <div class="card">
                    <div class="card-body">
                        <p>{% if search %}No records found matching your search for {{ academic_year_name }}.{% else %}No student records found for {{ academic_year_name }}.{% endif %}</p>
                    </div>
                </div>
            {% endif %}
        </div>

        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.js"></script>
        <script src="/static/js/core.js"></script>
        <script src="/static/js/student_parent_records.js"></script>
    </body>
    </html>
    ''',
    records=records,
    academic_years=academic_years,
    selected_academic_year=selected_academic_year,
    academic_year_name=academic_year_name,
    page=page,
    per_page=per_page,
    total_pages=total_pages,
    total_results=total_results,
    start=start,
    search=search
    )