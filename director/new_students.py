from flask import Blueprint, session, redirect, request, render_template_string, flash, get_flashed_messages
from functools import wraps
import mysql.connector
import sys
import os
from datetime import datetime
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
new_students_bp = Blueprint('new_students', __name__, url_prefix='/director')

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db():
    return mysql.connector.connect(**db_config)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def get_current_academic_year(conn):
    """Get current active academic year"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM academic_year WHERE is_active = 1 LIMIT 1")
    current = cursor.fetchone()
    cursor.close()
    
    if not current:
        # Fallback to latest year
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM academic_year ORDER BY year DESC LIMIT 1")
        current = cursor.fetchone()
        cursor.close()
    
    return current

def get_next_academic_year(conn, current_year):
    """Get next academic year"""
    if not current_year:
        return None
    
    current_year_num = int(current_year['year'].split('-')[0]) if '-' in current_year['year'] else int(current_year['year'])
    next_year_num = current_year_num + 1
    next_year_str = f"{next_year_num}-{next_year_num + 1}"
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM academic_year WHERE year = %s", (next_year_str,))
    next_year = cursor.fetchone()
    cursor.close()
    
    return next_year

def natural_sort_key(studid):
    """Create a sort key for natural sorting of student IDs"""
    if not studid:
        return (0, 0, 0, 0)
    parts = studid.split('/')
    try:
        prefix = parts[0] if len(parts) > 0 else ''
        grade = parts[1] if len(parts) > 1 else ''
        number = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        year = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
        return (prefix, grade, number, year)
    except:
        return (0, 0, 0, 0)

def get_new_section_id(conn, grade_id, section_index):
    """Get next section ID in round-robin fashion"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ID FROM section WHERE grade_id = %s ORDER BY ID", (grade_id,))
    sections = cursor.fetchall()
    cursor.close()
    
    if not sections:
        raise Exception(f"No sections available for grade {grade_id}")
    
    selected = sections[section_index % len(sections)]['ID']
    return selected

@new_students_bp.route('/new_students', methods=['GET', 'POST'])
@login_required
def new_students():
    """Student management page - view, add, and promote students"""
    
    # Only directors should access this
    if session.get('user_type') != 'director':
        return redirect('/unauthorized')
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get academic year information
    current_year = get_current_academic_year(conn)
    next_year = get_next_academic_year(conn, current_year)
    
    # Handle form submissions
    if request.method == 'POST':
        if 'promote_students' in request.form:
            promote_students(conn, current_year, next_year)
            # Refresh the page to show updated data
            return redirect('/director/new_students')
        elif 'add_student' in request.form:
            add_student(conn, request.form, current_year)
            return redirect('/director/new_students')
    
    # Get parameters
    search = request.args.get('search', '').strip()
    records_per_page = int(request.args.get('perPage', 10))
    page = int(request.args.get('page', 1))
    
    # Limit records per page between 5 and 50
    records_per_page = max(5, min(records_per_page, 50))
    
    # Build base query
    base_query = """
        SELECT 
            s.RN as student_RN, 
            e.studid,
            s.fullname,
            s.gender,
            s.parent_id,
            p.ID as parent_db_id,
            p.p_id,
            p.p_name,
            p.phone,
            p.email,
            g.level AS grade_name, 
            sec.sec_name AS section_name, 
            t.name AS teacher_name, 
            ay.year AS academic_year_date
        FROM student s
        JOIN enrollment e ON s.RN = e.student_RN 
            AND e.academic_year_id = s.academic_year_id
            AND e.grade_id = s.grade_id
            AND e.section_id = s.section_id
        LEFT JOIN parent p ON s.parent_id = p.ID
        LEFT JOIN grade g ON s.grade_id = g.ID
        LEFT JOIN section sec ON s.section_id = sec.ID
        LEFT JOIN teacher t ON s.teacher_id = t.ID
        LEFT JOIN academic_year ay ON s.academic_year_id = ay.ID
        WHERE s.academic_year_id = %s
    """
    params = [current_year['ID']] if current_year else []
    
    # Add search condition
    if search:
        base_query += " AND (e.studid LIKE %s OR s.fullname LIKE %s OR p.p_name LIKE %s)"
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as subquery"
    cursor.execute(count_query, params)
    total_students = cursor.fetchone()['total']
    
    # Calculate pagination
    total_pages = (total_students + records_per_page - 1) // records_per_page if total_students > 0 else 1
    page = max(1, min(page, total_pages))
    offset = (page - 1) * records_per_page
    
    # Main query with pagination
    query = base_query + " ORDER BY e.studid ASC LIMIT %s OFFSET %s"
    params.extend([records_per_page, offset])
    
    cursor.execute(query, params)
    students = cursor.fetchall()
    
    # Get all grades and sections for the add form
    cursor.execute("SELECT * FROM grade ORDER BY level ASC")
    grades = cursor.fetchall()
    
    cursor.execute("""
        SELECT MIN(ID) as ID, sec_name 
        FROM section 
        GROUP BY sec_name
        ORDER BY sec_name
    """)
    sections = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Prepare page range for pagination
    page_range = []
    max_visible = 5
    half = max_visible // 2
    start_page = max(1, page - half)
    end_page = min(total_pages, start_page + max_visible - 1)
    
    if end_page - start_page + 1 < max_visible:
        start_page = max(1, end_page - max_visible + 1)
    
    if start_page > 1:
        page_range.append(1)
        if start_page > 2:
            page_range.append('...')
    
    for i in range(start_page, end_page + 1):
        page_range.append(i)
    
    if end_page < total_pages:
        if end_page < total_pages - 1:
            page_range.append('...')
        page_range.append(total_pages)
    
    # Build query helper
    def build_query(additional_params):
        query_params = {}
        if search:
            query_params['search'] = search
        if records_per_page:
            query_params['perPage'] = records_per_page
        if 'page' in additional_params:
            query_params['page'] = additional_params['page']
        return '&'.join([f"{k}={v}" for k, v in query_params.items()])
    
    messages = get_flashed_messages(with_categories=True)
    
    return render_template_string(
        get_html_template(),
        current_year=current_year,
        next_year=next_year,
        students=students,
        total_students=total_students,
        page=page,
        total_pages=total_pages,
        page_range=page_range,
        records_per_page=records_per_page,
        search=search,
        grades=grades,
        sections=sections,
        build_query=build_query,
        messages=messages
    )


def promote_students(conn, current_year, next_year):
    """Promote all students to the next academic year"""
    if not current_year or not next_year:
        flash('Academic year information not found', 'error')
        return
    
    try:
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)
        
        # Get current students with their grades
        cursor.execute("""
            SELECT s.*, g.level as grade_name, sec.sec_name as section_name 
            FROM student s
            JOIN grade g ON s.grade_id = g.ID
            JOIN section sec ON s.section_id = sec.ID
            WHERE s.academic_year_id = %s
        """, (current_year['ID'],))
        students = cursor.fetchall()
        
        if not students:
            flash('No students to promote', 'warning')
            conn.rollback()
            cursor.close()
            return
        
        # Sort students naturally
        students.sort(key=lambda x: natural_sort_key(x.get('studid', '')))
        
        # Track section assignment for round-robin
        section_index = {}
        
        promoted_count = 0
        for student in students:
            new_grade_id = student['grade_id'] + 1
            
            # Get new section ID
            if new_grade_id not in section_index:
                section_index[new_grade_id] = 0
            
            try:
                new_section_id = get_new_section_id(conn, new_grade_id, section_index[new_grade_id])
                section_index[new_grade_id] += 1
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
                conn.rollback()
                cursor.close()
                return
            
            # Insert new record for next year
            cursor.execute("""
                INSERT INTO student (
                    studid, fullname, gender, age, is_blind, 
                    academic_year_id, grade_id, section_id, 
                    parent_id, s_address, photo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                student.get('studid', ''),
                student.get('fullname', ''),
                student.get('gender', ''),
                (student.get('age', 0) or 0) + 1,
                student.get('is_blind', 0),
                next_year['ID'],
                new_grade_id,
                new_section_id,
                student.get('parent_id'),
                student.get('s_address', ''),
                student.get('photo', '')
            ))
            promoted_count += 1
        
        conn.commit()
        cursor.close()
        flash(f'Successfully promoted {promoted_count} students to {next_year["year"]}', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error promoting students: {str(e)}', 'error')


def add_student(conn, form_data, current_year):
    """Add a new student"""
    if not current_year:
        flash('Academic year not found', 'error')
        return
    
    try:
        cursor = conn.cursor()
        
        # Get required fields
        studid = form_data.get('studid', '').strip()
        fullname = form_data.get('fullname', '').strip()
        gender = form_data.get('gender', '').strip()
        age = form_data.get('age', 0)
        grade_id = form_data.get('grade_id', 0)
        section_id = form_data.get('section_id', 0)
        parent_id = form_data.get('parent_id', '').strip()
        s_address = form_data.get('s_address', '').strip()
        is_blind = form_data.get('is_blind', 0)
        
        # Validate required fields
        if not studid or not fullname or not gender or not age or not grade_id or not section_id:
            flash('Please fill in all required fields', 'error')
            return
        
        cursor.execute("""
            INSERT INTO student (
                studid, fullname, gender, age, is_blind,
                academic_year_id, grade_id, section_id,
                parent_id, s_address
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            studid, fullname, gender, age, is_blind,
            current_year['ID'], grade_id, section_id,
            parent_id, s_address
        ))
        
        conn.commit()
        cursor.close()
        flash('Student added successfully!', 'success')
        
    except Exception as e:
        flash(f'Error adding student: {str(e)}', 'error')


def get_html_template():
    """Return the HTML template as a string"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Management</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .container { max-width: 1400px; margin: 0 auto; }
        .table-container { overflow-x: auto; }
        .pagination { flex-wrap: wrap; }
        @media (max-width: 768px) {
            .row { flex-direction: column; }
            .col-md-8, .col-md-4 { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1><i class="fas fa-users"></i> Student Management - {{ current_year.year if current_year else 'N/A' }}</h1>
        
        {% for category, message in messages %}
            <div class="alert alert-{{ 'success' if category == 'success' else 'danger' if category == 'error' else 'warning' }} alert-dismissible fade show" role="alert">
                {{ message }}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        {% endfor %}
        
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h4><i class="fas fa-list"></i> Current Students ({{ total_students }} total)</h4>
                    </div>
                    <div class="card-body">
                        <!-- Records per page selector -->
                        <div class="mb-3 d-flex justify-content-between align-items-center flex-wrap">
                            <form method="get" class="d-inline-flex gap-2">
                                <label for="perPage" class="me-2">Records per page:</label>
                                <select name="perPage" id="perPage" class="form-select form-select-sm" style="width: auto;" onchange="this.form.submit()">
                                    <option value="5" {{ 'selected' if records_per_page == 5 else '' }}>5</option>
                                    <option value="10" {{ 'selected' if records_per_page == 10 else '' }}>10</option>
                                    <option value="20" {{ 'selected' if records_per_page == 20 else '' }}>20</option>
                                    <option value="50" {{ 'selected' if records_per_page == 50 else '' }}>50</option>
                                </select>
                                {% if search %}
                                    <input type="hidden" name="search" value="{{ search }}">
                                {% endif %}
                            </form>
                        </div>
                        
                        <!-- Search Form -->
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5><i class="fas fa-search"></i> Search Students</h5>
                            </div>
                            <div class="card-body">
                                <form method="get" class="row g-3">
                                    <div class="col-md-8">
                                        <input type="text" class="form-control" name="search" 
                                               placeholder="Search by ID, Name, Grade, or Section"
                                               value="{{ search }}">
                                        <input type="hidden" name="perPage" value="{{ records_per_page }}">
                                    </div>
                                    <div class="col-md-4">
                                        <button type="submit" class="btn btn-primary me-2">Search</button>
                                        <a href="?perPage={{ records_per_page }}" class="btn btn-outline-secondary">Clear</a>
                                    </div>
                                </form>
                            </div>
                        </div>
                        
                        <!-- Students Table -->
                        <div class="table-container">
                            <table class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Student ID</th>
                                        <th>Name</th>
                                        <th>Grade</th>
                                        <th>Section</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for student in students %}
                                    <tr>
                                        <td>{{ loop.index + (page - 1) * records_per_page }}</td>
                                        <td>{{ student.studid or 'N/A' }}</td>
                                        <td>{{ student.fullname or 'N/A' }}</td>
                                        <td>{{ student.grade_name or 'N/A' }}</td>
                                        <td>{{ student.section_name or 'N/A' }}</td>
                                    </tr>
                                    {% else %}
                                    <tr>
                                        <td colspan="5" class="text-center">No students found</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        
                        <!-- Pagination -->
                        {% if total_pages > 1 %}
                        <nav aria-label="Page navigation" class="mt-3">
                            <ul class="pagination justify-content-center">
                                {% if page > 1 %}
                                <li class="page-item">
                                    <a class="page-link" href="?{{ build_query({'page': page - 1}) }}" aria-label="Previous">
                                        <span aria-hidden="true">&laquo;</span>
                                    </a>
                                </li>
                                {% endif %}
                                
                                {% for p in page_range %}
                                    {% if p == page %}
                                    <li class="page-item active"><span class="page-link">{{ p }}</span></li>
                                    {% elif p == '...' %}
                                    <li class="page-item disabled"><span class="page-link">...</span></li>
                                    {% else %}
                                    <li class="page-item"><a class="page-link" href="?{{ build_query({'page': p}) }}">{{ p }}</a></li>
                                    {% endif %}
                                {% endfor %}
                                
                                {% if page < total_pages %}
                                <li class="page-item">
                                    <a class="page-link" href="?{{ build_query({'page': page + 1}) }}" aria-label="Next">
                                        <span aria-hidden="true">&raquo;</span>
                                    </a>
                                </li>
                                {% endif %}
                            </ul>
                        </nav>
                        {% endif %}
                        
                        <!-- Promote Button -->
                        {% if next_year %}
                        <form method="post" class="mt-3">
                            <button type="submit" name="promote_students" class="btn btn-primary"
                                    onclick="return confirm('Promote all students to {{ next_year.year }}?')">
                                <i class="fas fa-arrow-up"></i> Promote Students to {{ next_year.year }}
                            </button>
                        </form>
                        {% endif %}
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h4><i class="fas fa-user-plus"></i> Add New Student</h4>
                    </div>
                    <div class="card-body">
                        <form method="post">
                            <div class="mb-3">
                                <label class="form-label">Student ID</label>
                                <input type="text" name="studid" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Full Name</label>
                                <input type="text" name="fullname" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Gender</label>
                                <select name="gender" class="form-select" required>
                                    <option value="M">Male</option>
                                    <option value="F">Female</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Age</label>
                                <input type="number" name="age" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Grade</label>
                                <select name="grade_id" class="form-select" required>
                                    {% for grade in grades %}
                                    <option value="{{ grade.ID }}">{{ grade.level }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Section</label>
                                <select name="section_id" class="form-select" required>
                                    {% for section in sections %}
                                    <option value="{{ section.ID }}">{{ section.sec_name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Parent ID</label>
                                <input type="text" name="parent_id" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Address</label>
                                <input type="text" name="s_address" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <div class="form-check">
                                    <input type="checkbox" name="is_blind" value="1" class="form-check-input" id="is_blind">
                                    <label class="form-check-label" for="is_blind">Is Blind</label>
                                </div>
                            </div>
                            <button type="submit" name="add_student" class="btn btn-success w-100">
                                <i class="fas fa-save"></i> Add Student
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    '''

def flash(message, category='success'):
    """Simple flash message function"""
    from flask import flash as flask_flash
    flask_flash(message, category)