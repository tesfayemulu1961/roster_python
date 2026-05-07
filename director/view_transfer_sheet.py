# ==============================================
# view_transfer_sheet.py - FIXED PAGINATION
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
    
    # Get filter values
    year_id = request.args.get('year', type=int)
    grade_id = request.args.get('grade', type=int)
    section_id = request.args.get('section', type=int)
    teacher_id = request.args.get('teacher', type=int)
    subject_id = request.args.get('subject', type=int)
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    offset = (page - 1) * per_page
    
    # Fetch dropdown options - Use GROUP BY to remove duplicates
    cursor.execute("SELECT ID, year FROM academic_year GROUP BY year ORDER BY year DESC")
    academic_years = cursor.fetchall()
    
    cursor.execute("SELECT ID, level FROM grade GROUP BY level ORDER BY ID")
    grades = cursor.fetchall()
    
    # Use GROUP BY sec_name to remove duplicate sections
    cursor.execute("SELECT MIN(ID) as ID, sec_name FROM section GROUP BY sec_name ORDER BY sec_name")
    sections = cursor.fetchall()
    
    cursor.execute("SELECT ID, name FROM teacher GROUP BY name ORDER BY name")
    teachers = cursor.fetchall()
    
    cursor.execute("SELECT ID, sub_code, sub_name FROM subject GROUP BY sub_code ORDER BY sub_code")
    subjects = cursor.fetchall()
    
    # Build WHERE clause
    where_parts = []
    params = []
    
    if year_id:
        where_parts.append("a.academic_year_id = %s")
        params.append(year_id)
    if grade_id:
        where_parts.append("a.grade_id = %s")
        params.append(grade_id)
    if section_id:
        where_parts.append("a.section_id = %s")
        params.append(section_id)
    if teacher_id:
        where_parts.append("a.teacher_id = %s")
        params.append(teacher_id)
    if subject_id:
        where_parts.append("a.subject_id = %s")
        params.append(subject_id)
    
    where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else "WHERE 1=1"
    
    # Count query for pagination - get total number of unique student-subject combinations
    count_query = f"""
        SELECT COUNT(DISTINCT CONCAT(a.student_RN, '-', a.subject_id)) as total
        FROM assessment a
        JOIN student s ON a.student_RN = s.RN
        JOIN academic_year ay ON a.academic_year_id = ay.ID
        JOIN grade g ON a.grade_id = g.ID
        JOIN section sec ON a.section_id = sec.ID
        JOIN teacher t ON a.teacher_id = t.ID
        JOIN subject sub ON a.subject_id = sub.ID
        {where_clause}
    """
    cursor.execute(count_query, tuple(params))
    result = cursor.fetchone()
    total_count = result['total'] if result and result['total'] else 0
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    
    # For debugging - print to console
    print(f"Total count: {total_count}, Per page: {per_page}, Total pages: {total_pages}, Page: {page}")
    
    # Main query with pagination
    query = f"""
        SELECT 
            a.academic_year_id, 
            a.teacher_id, 
            a.grade_id, 
            a.section_id, 
            a.student_RN, 
            s.RN as student_rn,
            s.fullname,
            s.gender,
            s.age,
            s.is_blind,
            ay.year AS academic_year,
            g.level AS grade,
            sec.sec_name AS section,
            t.name AS teacher,
            sub.sub_code AS subject,
            sub.sub_name as subject_name,
            MAX(CASE WHEN a.semester = '1' THEN a.sum_40 ELSE NULL END) AS fs_40,
            MAX(CASE WHEN a.semester = '1' THEN a.exam_60 ELSE NULL END) AS fs_60,
            MAX(CASE WHEN a.semester = '1' THEN a.total_100 ELSE NULL END) AS fs_100,
            MAX(CASE WHEN a.semester = '2' THEN a.sum_40 ELSE NULL END) AS ss_40,
            MAX(CASE WHEN a.semester = '2' THEN a.exam_60 ELSE NULL END) AS ss_60,
            MAX(CASE WHEN a.semester = '2' THEN a.total_100 ELSE NULL END) AS ss_100
        FROM assessment a
        JOIN student s ON a.student_RN = s.RN
        JOIN academic_year ay ON a.academic_year_id = ay.ID
        JOIN grade g ON a.grade_id = g.ID
        JOIN section sec ON a.section_id = sec.ID
        JOIN teacher t ON a.teacher_id = t.ID
        JOIN subject sub ON a.subject_id = sub.ID
        {where_clause}
        GROUP BY a.academic_year_id, a.teacher_id, a.grade_id, a.section_id, a.student_RN, a.subject_id
        ORDER BY s.fullname, sub.sub_code
        LIMIT %s OFFSET %s
    """
    
    cursor.execute(query, tuple(params + [per_page, offset]))
    transfer_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Create URL base for pagination
    def build_url(page_num):
        return f"?page={page_num}&per_page={per_page}&year={year_id or ''}&grade={grade_id or ''}&section={section_id or ''}&teacher={teacher_id or ''}&subject={subject_id or ''}"
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Transfer Sheet - Score Report</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="{{ url_for('static', filename='css/common.css') }}">
        <style>
            .container-narrow {
                max-width: 1200px;
                margin: 0 auto;
            }
            .blind-row {
                background-color: #fff3cd !important;
            }
            .table-sm td, .table-sm th {
                padding: 0.5rem;
                font-size: 0.85rem;
            }
            .pagination-wrapper {
                display: flex;
                justify-content: center;
                gap: 6px;
                margin-top: 20px;
                margin-bottom: 20px;
            }
            .page-btn {
                padding: 8px 14px;
                background: white;
                border: 1px solid #dee2e6;
                color: #0d6efd;
                text-decoration: none;
                font-size: 0.9rem;
                border-radius: 6px;
                transition: all 0.2s;
                cursor: pointer;
                display: inline-block;
            }
            .page-btn:hover {
                background: #0d6efd;
                color: white;
                border-color: #0d6efd;
            }
            .page-btn.active {
                background: #0d6efd;
                color: white;
                border-color: #0d6efd;
                cursor: default;
            }
            .per-page-selector {
                width: auto;
                display: inline-block;
            }
            .stats-bar {
                background: #f8f9fa;
                padding: 12px 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 10px;
            }
            .stats-bar strong {
                color: #0d6efd;
                font-size: 1.1rem;
            }
        </style>
    </head>
    <body>
        <div class="container-narrow py-3">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4><i class="fas fa-exchange-alt"></i> Transfer Sheet - Score Report</h4>
                <a href="/director/director_dashboard" class="btn btn-secondary btn-sm">Back to Dashboard</a>
            </div>
            
            <div class="card mb-3">
                <div class="card-body">
                    <form method="GET" class="row g-3" id="filterForm">
                        <div class="col-md-2">
                            <label class="form-label">Academic Year</label>
                            <select name="year" class="form-select" onchange="this.form.submit()">
                                <option value="">-- Select --</option>
                                {% for ay in academic_years %}
                                    <option value="{{ ay.ID }}" {% if request.args.get('year')|int == ay.ID %}selected{% endif %}>{{ ay.year }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Grade</label>
                            <select name="grade" class="form-select" onchange="this.form.submit()">
                                <option value="">-- Select --</option>
                                {% for g in grades %}
                                    <option value="{{ g.ID }}" {% if request.args.get('grade')|int == g.ID %}selected{% endif %}>{{ g.level }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Section</label>
                            <select name="section" class="form-select" onchange="this.form.submit()">
                                <option value="">-- Select --</option>
                                {% for s in sections %}
                                    <option value="{{ s.ID }}" {% if request.args.get('section')|int == s.ID %}selected{% endif %}>{{ s.sec_name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Teacher</label>
                            <select name="teacher" class="form-select" onchange="this.form.submit()">
                                <option value="">-- Select --</option>
                                {% for t in teachers %}
                                    <option value="{{ t.ID }}" {% if request.args.get('teacher')|int == t.ID %}selected{% endif %}>{{ t.name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Subject</label>
                            <select name="subject" class="form-select" onchange="this.form.submit()">
                                <option value="">-- Select --</option>
                                {% for sub in subjects %}
                                    <option value="{{ sub.ID }}" {% if request.args.get('subject')|int == sub.ID %}selected{% endif %}>{{ sub.sub_code }} - {{ sub.sub_name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-2 d-flex align-items-end gap-2">
                            <button type="submit" class="btn btn-primary w-100"><i class="fas fa-search"></i> Search</button>
                            <a href="/director/view_transfer_sheet" class="btn btn-secondary w-100"><i class="fas fa-times"></i> Clear</a>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Stats Bar - Always visible -->
            <div class="stats-bar">
                <div>
                    <i class="fas fa-chart-line"></i> 
                    <strong>{{ transfer_data|length }}</strong> records on this page | 
                    <strong>{{ total_count }}</strong> total records | 
                    <strong>{{ total_pages }}</strong> pages
                </div>
                <div>
                    <label class="me-2"><i class="fas fa-eye"></i> Show:</label>
                    <select class="form-select form-select-sm per-page-selector" onchange="window.location.href=updatePerPage(this.value)">
                        <option value="15" {% if per_page == 15 %}selected{% endif %}>15 per page</option>
                        <option value="25" {% if per_page == 25 %}selected{% endif %}>25 per page</option>
                        <option value="50" {% if per_page == 50 %}selected{% endif %}>50 per page</option>
                        <option value="100" {% if per_page == 100 %}selected{% endif %}>100 per page</option>
                    </select>
                </div>
            </div>
            
            <!-- Data Table -->
            {% if transfer_data and transfer_data|length > 0 %}
            <div class="card">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-sm table-striped table-hover" style="width:100%">
                            <thead class="table-dark">
                                <tr>
                                    <th>#</th>
                                    <th>Student ID</th>
                                    <th>Full Name</th>
                                    <th>Gender</th>
                                    <th>Age</th>
                                    <th>1st Sem (40%)</th>
                                    <th>1st Sem (60%)</th>
                                    <th>1st Sem (100%)</th>
                                    <th>2nd Sem (40%)</th>
                                    <th>2nd Sem (60%)</th>
                                    <th>2nd Sem (100%)</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for row in transfer_data %}
                                <tr {% if row.is_blind %}class="blind-row"{% endif %}>
                                    <td>{{ loop.index + (page - 1) * per_page }}</td>
                                    <td>{{ row.student_rn }}</td>
                                    <td>{{ row.fullname }}</td>
                                    <td>{{ row.gender or '—' }}</td>
                                    <td>{{ row.age or '—' }}</td>
                                    <td>{{ row.fs_40 or '-' }}</td>
                                    <td>{{ row.fs_60 or '-' }}</td>
                                    <td>{{ row.fs_100 or '-' }}</td>
                                    <td>{{ row.ss_40 or '-' }}</td>
                                    <td>{{ row.ss_60 or '-' }}</td>
                                    <td>{{ row.ss_100 or '-' }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- Pagination - Show when more than 1 page -->
            {% if total_pages > 1 %}
            <div class="pagination-wrapper">
                {% if page > 1 %}
                    <a href="?page={{ page-1 }}&per_page={{ per_page }}&year={{ year_id or '' }}&grade={{ grade_id or '' }}&section={{ section_id or '' }}&teacher={{ teacher_id or '' }}&subject={{ subject_id or '' }}" 
                       class="page-btn">
                        <i class="fas fa-chevron-left"></i> Prev
                    </a>
                {% endif %}
                
                {% set start_page = [page-2, 1]|max %}
                {% set end_page = [page+2, total_pages]|min %}
                
                {% for p in range(start_page, end_page + 1) %}
                    {% if p == page %}
                        <span class="page-btn active">{{ p }}</span>
                    {% else %}
                        <a href="?page={{ p }}&per_page={{ per_page }}&year={{ year_id or '' }}&grade={{ grade_id or '' }}&section={{ section_id or '' }}&teacher={{ teacher_id or '' }}&subject={{ subject_id or '' }}" 
                           class="page-btn">{{ p }}</a>
                    {% endif %}
                {% endfor %}
                
                {% if page < total_pages %}
                    <a href="?page={{ page+1 }}&per_page={{ per_page }}&year={{ year_id or '' }}&grade={{ grade_id or '' }}&section={{ section_id or '' }}&teacher={{ teacher_id or '' }}&subject={{ subject_id or '' }}" 
                       class="page-btn">
                        Next <i class="fas fa-chevron-right"></i>
                    </a>
                {% endif %}
            </div>
            {% endif %}
            
            {% else %}
            <div class="alert alert-info text-center">
                <i class="fas fa-info-circle fa-2x mb-2 d-block"></i>
                <h5>No data found</h5>
                <p>Please select filters above and click Search to display results.</p>
            </div>
            {% endif %}
        </div>
        
        <script>
            function updatePerPage(value) {
                const urlParams = new URLSearchParams(window.location.search);
                urlParams.set('per_page', value);
                urlParams.set('page', 1);
                window.location.search = urlParams.toString();
            }
            
            // Debug info
            console.log('Total pages: {{ total_pages }}');
            console.log('Total count: {{ total_count }}');
            console.log('Current page: {{ page }}');
        </script>
        
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="{{ url_for('static', filename='js/common.js') }}"></script>
    </body>
    </html>
    ''',
    academic_years=academic_years,
    grades=grades,
    sections=sections,
    teachers=teachers,
    subjects=subjects,
    transfer_data=transfer_data,
    page=page,
    total_pages=total_pages,
    per_page=per_page,
    total_count=total_count,
    year_id=year_id,
    grade_id=grade_id,
    section_id=section_id,
    teacher_id=teacher_id,
    subject_id=subject_id
    )