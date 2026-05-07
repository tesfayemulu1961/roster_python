# ==============================================
# view_student_roster.py - FIXED (removed <\/td> tags)
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request, Response
from functools import wraps
import mysql.connector
import math
import csv
from io import StringIO
import re

director_view_student_roster = Blueprint('director_view_student_roster', __name__, url_prefix='/director')

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

def get_student_number(studid):
    """Extract numeric part from studid"""
    if studid:
        parts = studid.split('/')
        if len(parts) >= 4:
            try:
                return int(parts[3])
            except:
                return 0
    return 0

def get_failed_students_count(cursor, year_id, grade_id, section_id):
    """Count failed students in a section based on second semester scores"""
    try:
        cursor.execute("""
            SELECT COUNT(DISTINCT s.RN) as fail_count
            FROM student s
            JOIN student_scores sc ON s.RN = sc.student_RN 
                AND sc.academic_year_id = s.academic_year_id
                AND sc.grade_id = s.grade_id
                AND sc.section_id = s.section_id
            WHERE s.academic_year_id = %s
              AND s.grade_id = %s
              AND s.section_id = %s
              AND sc.semester = '2'
              AND sc.total_100 < 50
        """, (year_id, grade_id, section_id))
        result = cursor.fetchone()
        return result['fail_count'] if result else 0
    except:
        return 0

@director_view_student_roster.route('/view_student_roster')
@login_required
def view_student_roster_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get filter values
    year_id = request.args.get('year', 0, type=int)
    grade_id = request.args.get('grade', 0, type=int)
    section_id = request.args.get('section', 0, type=int)
    semester = request.args.get('semester', '1')
    search_term = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Initialize variables
    students = []
    total_rows = 0
    total_pages = 1
    failed_count = 0
    ethiopian_year = "Unknown"
    grade_name = ""
    section_name = ""
    room_teacher_name = "Not Assigned"
    room_teacher_id = 0
    
    # CSV Export
    if request.args.get('export') == 'csv' and year_id and grade_id and section_id:
        return export_to_csv(conn, year_id, grade_id, section_id, search_term)
    
    # Fetch dropdown options
    cursor.execute("SELECT ID, year, ec_year FROM academic_year ORDER BY year DESC")
    academic_years = cursor.fetchall()
    
    cursor.execute("SELECT ID, level FROM grade ORDER BY ID")
    grades = cursor.fetchall()
    
    # Get sections for selected grade
    section_options = []
    if grade_id:
        cursor.execute("SELECT ID, sec_name FROM section WHERE grade_id = %s ORDER BY sec_name", (grade_id,))
        section_options = cursor.fetchall()
    
    # Get grade and section names
    if grade_id:
        cursor.execute("SELECT level FROM grade WHERE ID = %s", (grade_id,))
        result = cursor.fetchone()
        if result:
            grade_name = result['level']
    if section_id:
        cursor.execute("SELECT sec_name FROM section WHERE ID = %s", (section_id,))
        result = cursor.fetchone()
        if result:
            section_name = result['sec_name']
    
    # Get Ethiopian year
    if year_id:
        cursor.execute("SELECT ec_year FROM academic_year WHERE ID = %s", (year_id,))
        result = cursor.fetchone()
        if result:
            ethiopian_year = result['ec_year']
    else:
        cursor.execute("SELECT ec_year FROM academic_year WHERE is_active = 1 LIMIT 1")
        result = cursor.fetchone()
        if result:
            ethiopian_year = result['ec_year']
    
    # Get room teacher
    if section_id and year_id:
        try:
            cursor.execute("""
                SELECT t.name 
                FROM teacher_assignment ta
                INNER JOIN teacher t ON ta.teacher_id = t.ID
                WHERE ta.section_id = %s AND ta.academic_year_id = %s AND ta.is_room_teacher = 1
                LIMIT 1
            """, (section_id, year_id))
            result = cursor.fetchone()
            if result:
                room_teacher_name = result['name']
        except:
            pass
    
    # Process students if all filters selected
    show_results = (year_id and grade_id and section_id)
    
    if show_results:
        try:
            # Determine subjects based on grade level
            if grade_id >= 11 and grade_id <= 12:
                subjects = ['Amh', 'Eng', 'Maths', 'GSc', 'SSc', 'Ctzp', 'IT', 'Arts', 'HPE', 'CTE']
            else:
                subjects = ['Amh', 'Eng', 'Maths', 'EnSc', 'Arts', 'HPE', 'Ethics']
            
            subject_count = len(subjects)
            
            # Build the SELECT columns for dynamic subjects
            f_selects = [f"s1.`{sub}` AS f_{sub}" for sub in subjects]
            s_selects = [f"s2.`{sub}` AS s_{sub}" for sub in subjects]
            
            # Main query - get all students with scores for both semesters
            query = f"""
                SELECT 
                    e.student_RN as RN,
                    e.studid, 
                    s.fullname, 
                    s.gender, 
                    s.age,
                    {', '.join(f_selects)},
                    {', '.join(s_selects)}
                FROM enrollment e
                INNER JOIN student s ON e.student_RN = s.RN
                LEFT JOIN student_scores s1 ON s.RN = s1.student_RN AND s1.semester = '1' 
                    AND s1.academic_year_id = e.academic_year_id 
                    AND s1.grade_id = e.grade_id 
                    AND s1.section_id = e.section_id
                LEFT JOIN student_scores s2 ON s.RN = s2.student_RN AND s2.semester = '2' 
                    AND s2.academic_year_id = e.academic_year_id 
                    AND s2.grade_id = e.grade_id 
                    AND s2.section_id = e.section_id
                WHERE e.academic_year_id = %s 
                  AND e.grade_id = %s
                  AND e.section_id = %s
            """
            params = [year_id, grade_id, section_id]
            
            if search_term:
                query += " AND (s.fullname LIKE %s OR e.studid LIKE %s)"
                search_param = f"%{search_term}%"
                params.extend([search_param, search_param])
            
            cursor.execute(query, tuple(params))
            all_results = cursor.fetchall()
            
            # Process each student
            all_students = []
            for row in all_results:
                # First semester scores
                f_scores = []
                f_sum = 0
                for sub in subjects:
                    val = row.get(f'f_{sub}')
                    f_scores.append(val)
                    if val is not None:
                        f_sum += val
                
                f_sum_val = f_sum if f_sum > 0 else None
                f_avg = round(f_sum / subject_count, 2) if f_sum > 0 else None
                if f_avg == 0:
                    f_avg = None
                    f_sum_val = None
                
                # Second semester scores
                s_scores = []
                s_sum = 0
                for sub in subjects:
                    val = row.get(f's_{sub}')
                    s_scores.append(val)
                    if val is not None:
                        s_sum += val
                
                s_sum_val = s_sum if s_sum > 0 else None
                s_avg = round(s_sum / subject_count, 2) if s_sum > 0 else None
                if s_avg == 0:
                    s_avg = None
                    s_sum_val = None
                
                # Average scores (for average row)
                a_scores = []
                a_sum = 0
                for i in range(subject_count):
                    if f_scores[i] is not None and s_scores[i] is not None:
                        avg_val = round((f_scores[i] + s_scores[i]) / 2, 2)
                        a_scores.append(avg_val)
                        a_sum += avg_val
                    elif f_scores[i] is not None:
                        a_scores.append(f_scores[i])
                        a_sum += f_scores[i]
                    elif s_scores[i] is not None:
                        a_scores.append(s_scores[i])
                        a_sum += s_scores[i]
                    else:
                        a_scores.append(None)
                
                a_sum_val = a_sum if a_sum > 0 else None
                a_avg = round(a_sum / subject_count, 2) if a_sum > 0 else None
                if a_avg == 0:
                    a_avg = None
                    a_sum_val = None
                
                # Overall average for remark
                overall_avg = None
                if f_avg is not None and s_avg is not None:
                    overall_avg = round((f_avg + s_avg) / 2, 2)
                elif f_avg is not None:
                    overall_avg = f_avg
                elif s_avg is not None:
                    overall_avg = s_avg
                
                remark = 'Passed' if overall_avg is not None and overall_avg >= 50 else 'Failed'
                student_num = get_student_number(row['studid'])
                
                all_students.append({
                    'data': row,
                    'student_num': student_num,
                    'f_scores': f_scores,
                    's_scores': s_scores,
                    'a_scores': a_scores,
                    'f_sum': f_sum_val,
                    's_sum': s_sum_val,
                    'a_sum': a_sum_val,
                    'f_avg': f_avg,
                    's_avg': s_avg,
                    'a_avg': a_avg,
                    'subject_count': subject_count,
                    'remark': remark
                })
            
            # Calculate ranks for each type of average
            for field in ['f_avg', 's_avg', 'a_avg']:
                students_with_values = [s for s in all_students if s[field] is not None]
                students_with_values.sort(key=lambda x: x[field], reverse=True)
                rank = 1
                prev_value = None
                for idx, student in enumerate(students_with_values):
                    if prev_value is not None and student[field] < prev_value:
                        rank = idx + 1
                    student[f'{field}_rank'] = rank
                    prev_value = student[field]
                
                # Set rank for students without values
                for student in all_students:
                    if f'{field}_rank' not in student:
                        student[f'{field}_rank'] = None
            
            # Sort by student number
            all_students.sort(key=lambda x: x['student_num'])
            
            total_rows = len(all_students)
            total_pages = math.ceil(total_rows / per_page) if total_rows > 0 else 1
            offset = (page - 1) * per_page
            students = all_students[offset:offset + per_page]
            
            # Get failed students count
            failed_count = get_failed_students_count(cursor, year_id, grade_id, section_id)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Student Roster Management</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --primary: #7c3aed;
                --primary-dark: #6d28d9;
                --danger: #dc3545;
                --danger-dark: #c82333;
                --gray-light: #e2e8f0;
                --gray-dark: #64748b;
                --text: #334155;
                --text-light: #475569;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8fafc;
                padding: 20px;
                color: var(--text);
                line-height: 1.6;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            .page-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 2rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid var(--gray-light);
            }
            
            .page-header h1 {
                font-size: 1.8rem;
                font-weight: 600;
                margin: 0;
                display: flex;
                align-items: center;
                gap: 0.75rem;
                color: #1e293b;
            }
            
            .search-form {
                background: white;
                padding: 1.75rem;
                border-radius: 0.75rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                margin-bottom: 2rem;
                border: 1px solid var(--gray-light);
                max-width: 800px;
                margin: 0 auto 2rem;
            }
            
            .form-row {
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
                margin-bottom: 1.25rem;
            }
            
            .form-group {
                flex: 1;
                min-width: 180px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
                color: var(--text-light);
                font-size: 0.9375rem;
            }
            
            .form-control {
                width: 100%;
                padding: 0.625rem 0.875rem;
                border: 1px solid var(--gray-light);
                border-radius: 0.5rem;
                font-size: 0.9375rem;
                transition: all 0.2s ease;
                background-color: #fff;
            }
            
            .form-control:focus {
                outline: none;
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
            }
            
            .btn {
                padding: 0.625rem 1.25rem;
                border: none;
                border-radius: 0.5rem;
                cursor: pointer;
                font-size: 0.9375rem;
                font-weight: 500;
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                text-decoration: none;
                transition: all 0.2s ease;
            }
            
            .btn-primary {
                background-color: var(--primary);
                color: white;
            }
            
            .btn-primary:hover {
                background-color: var(--primary-dark);
                transform: translateY(-1px);
            }
            
            .btn-danger {
                background-color: var(--danger);
                color: white;
            }
            
            .btn-danger:hover {
                background-color: var(--danger-dark);
                transform: translateY(-1px);
            }
            
            .form-actions {
                display: flex;
                gap: 0.75rem;
                margin-top: 1rem;
            }
            
            .results-container {
                background: white;
                border-radius: 0.75rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                padding: 1.75rem;
                overflow-x: auto;
                border: 1px solid var(--gray-light);
                margin-bottom: 2rem;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
            }
            
            th {
                background-color: #f1f5f9;
                color: var(--text);
                font-weight: 600;
                text-align: center;
                padding: 0.75rem 0.5rem;
                font-size: 0.875rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border: 1px solid var(--gray-light);
            }
            
            td {
                padding: 0.5rem;
                border: 1px solid var(--gray-light);
                text-align: center;
                font-size: 0.875rem;
            }
            
            tr:hover {
                background-color: #f8fafc;
            }
            
            .alert {
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1.5rem;
            }
            
            .alert-danger {
                background-color: #fee2e2;
                color: #b91c1c;
                border: 1px solid #fca5a5;
            }
            
            .header-info {
                margin-bottom: 20px;
                text-align: center;
            }
            
            .header-info h3 {
                margin-bottom: 5px;
                color: #2c3e50;
            }
            
            .header-info h4 {
                margin-top: 0;
                color: #4a5568;
                font-weight: normal;
            }
            
            .semester-1st {
                background-color: #f8f9fa;
            }
            .semester-2nd {
                background-color: #e9ecef;
            }
            .semester-avr {
                background-color: #dee2e6;
                font-weight: bold;
            }
            .summary-cell {
                background-color: #ced4da;
                font-weight: bold;
            }
            .pass {
                color: #28a745;
                font-weight: bold;
            }
            .fail {
                color: #dc3545;
                font-weight: bold;
            }
            
            .pagination {
                display: flex;
                justify-content: center;
                margin-top: 20px;
                gap: 5px;
            }
            .page-link {
                padding: 8px 12px;
                text-decoration: none;
                color: #2196F3;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .page-link:hover {
                background-color: #f1f1f1;
            }
            .current-page {
                padding: 8px 12px;
                background-color: #2196F3;
                color: white;
                border: 1px solid #2196F3;
                border-radius: 4px;
            }
            
            .null-value {
                color: #dc3545;
                font-style: italic;
            }
            
            .low-score {
                background-color: #ffebee;
                color: #c62828;
            }
            
            .search-box {
                margin-bottom: 20px;
                text-align: right;
            }
            
            .search-box input {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                width: 250px;
            }
            
            .export-buttons {
                margin-bottom: 20px;
                display: flex;
                gap: 10px;
            }
            
            @media (max-width: 768px) {
                .search-form {
                    max-width: 100%;
                    padding: 1.25rem;
                }
                
                .form-row {
                    flex-direction: column;
                    gap: 1rem;
                }
                
                .form-group {
                    min-width: 100%;
                }
                
                .export-buttons {
                    flex-direction: column;
                }
                
                .search-box input {
                    width: 100%;
                    margin-bottom: 10px;
                }
            }
            
            @media print {
                .search-form, .export-buttons, .search-box, .pagination, .form-actions {
                    display: none;
                }
                body {
                    background-color: white;
                    padding: 0;
                }
                .container {
                    max-width: 100%;
                    padding: 0;
                }
                .results-container {
                    padding: 0;
                    box-shadow: none;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="page-header">
                <h1><i class="fas fa-users"></i> Student Roster Report</h1>
            </div>

            {% if not (year_id and grade_id and section_id) %}
            <div class="search-form">
                <h2><i class="fas fa-filter"></i> Filter Students</h2>
                <form method="GET" id="filterForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Academic Year</label>
                            <select name="year" class="form-control" required id="yearSelect">
                                <option value="">-- Select --</option>
                                {% for ay in academic_years %}
                                    <option value="{{ ay.ID }}" {% if year_id == ay.ID %}selected{% endif %}>{{ ay.year }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Grade</label>
                            <select name="grade" class="form-control" required id="gradeSelect">
                                <option value="">-- Select --</option>
                                {% for g in grades %}
                                    <option value="{{ g.ID }}" {% if grade_id == g.ID %}selected{% endif %}>{{ g.level }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Section</label>
                            <select name="section" class="form-control" required id="sectionSelect">
                                <option value="">-- Select --</option>
                                {% for s in section_options %}
                                    <option value="{{ s.ID }}" {% if section_id == s.ID %}selected{% endif %}>{{ s.sec_name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Semester</label>
                            <select name="semester" class="form-control" required>
                                <option value="1" {% if semester == '1' %}selected{% endif %}>First Semester</option>
                                <option value="2" {% if semester == '2' %}selected{% endif %}>Second Semester</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-search"></i> Search
                        </button>
                        <a href="/director/view_student_roster" class="btn btn-danger">
                            <i class="fas fa-times"></i> Clear
                        </a>
                    </div>
                </form>
            </div>
            {% endif %}

            {% if show_results %}
            <div class="export-buttons">
                <a href="?year={{ year_id }}&grade={{ grade_id }}&section={{ section_id }}&export=csv" class="btn btn-primary">
                    <i class="fas fa-file-csv"></i> Export to CSV
                </a>
                <button onclick="window.print()" class="btn btn-primary">
                    <i class="fas fa-print"></i> Print Report
                </button>
            </div>

            <div class="search-box">
                <form method="GET">
                    <input type="hidden" name="year" value="{{ year_id }}">
                    <input type="hidden" name="grade" value="{{ grade_id }}">
                    <input type="hidden" name="section" value="{{ section_id }}">
                    <input type="hidden" name="semester" value="{{ semester }}">
                    <input type="text" name="search" placeholder="Search students..." value="{{ search_term }}">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-search"></i> Search
                    </button>
                    <a href="?year={{ year_id }}&grade={{ grade_id }}&section={{ section_id }}&semester={{ semester }}" class="btn btn-danger">
                        <i class="fas fa-times"></i> Clear
                    </a>
                </form>
            </div>

            <div class="header-info">
                <h3>Melkakole First and Medium School: Student Roster</h3>
                <h4>
                    Academic Year: <b><u>{{ ethiopian_year }}</u></b> &nbsp; &nbsp;
                    Grade: <b><u>{{ grade_name }}</u></b> &nbsp; &nbsp;
                    Section: <b><u>{{ section_name }}</u></b> &nbsp; &nbsp; 
                    Teacher: <b><u>{{ room_teacher_name }}</u></b> &nbsp; &nbsp;
                    Failed Students: <b><u>{{ failed_count }}</u></b>
                </h4>
            </div>

            {% if students and students|length > 0 %}
            <div class="results-container">
                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>RN</th>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Gender</th>
                                <th>Age</th>
                                <th>Sem</th>
                                {% for subject in students[0].f_scores %}
                                    <th>{{ loop.index0 }}</th>
                                {% endfor %}
                                <th>Sum</th>
                                <th>Avg</th>
                                <th>Rank</th>
                                <th>Remark</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for student in students %}
                                {% set row = student.data %}
                                <tr class="semester-1st">
                                    <td rowspan="3">{{ row.RN }}</td>
                                    <td rowspan="3">{{ row.studid }}</td>
                                    <td rowspan="3">{{ row.fullname }}</td>
                                    <td rowspan="3">{{ row.gender or '—' }}</td>
                                    <td rowspan="3">{{ row.age or '—' }}</td>
                                    <td>1st</td>
                                    {% for val in student.f_scores %}
                                        <td class="{% if val is not none and val < 50 %}low-score{% endif %} {% if val is none %}null-value{% endif %}">
                                            {{ val if val is not none else 'NULL' }}
                                        </td>
                                    {% endfor %}
                                    <td class="summary-cell">{{ student.f_sum if student.f_sum is not none else 'NULL' }}</td>
                                    <td class="summary-cell">{{ student.f_avg if student.f_avg is not none else 'NULL' }}</td>
                                    <td class="summary-cell">{{ student.f_avg_rank or 'NULL' }}</td>
                                    <td rowspan="3" class="{{ 'pass' if student.remark == 'Passed' else 'fail' }}">{{ student.remark }}</td>
                                </tr>
                                <tr class="semester-2nd">
                                    <td>2nd</td>
                                    {% for val in student.s_scores %}
                                        <td class="{% if val is not none and val < 50 %}low-score{% endif %} {% if val is none %}null-value{% endif %}">
                                            {{ val if val is not none else 'NULL' }}
                                        </td>
                                    {% endfor %}
                                    <td class="summary-cell">{{ student.s_sum if student.s_sum is not none else 'NULL' }}</td>
                                    <td class="summary-cell">{{ student.s_avg if student.s_avg is not none else 'NULL' }}</td>
                                    <td class="summary-cell">{{ student.s_avg_rank or 'NULL' }}</td>
                                </tr>
                                <tr class="semester-avr">
                                    <td>Avg</td>
                                    {% for val in student.a_scores %}
                                        <td class="{% if val is not none and val < 50 %}low-score{% endif %} {% if val is none %}null-value{% endif %}">
                                            {{ val if val is not none else 'NULL' }}
                                        </td>
                                    {% endfor %}
                                    <td class="summary-cell">{{ student.a_sum if student.a_sum is not none else 'NULL' }}</td>
                                    <td class="summary-cell">{{ student.a_avg if student.a_avg is not none else 'NULL' }}</td>
                                    <td class="summary-cell">{{ student.a_avg_rank or 'NULL' }}</td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            
            {% if total_pages > 1 %}
            <div class="pagination">
                {% if page > 1 %}
                    <a href="?year={{ year_id }}&grade={{ grade_id }}&section={{ section_id }}&search={{ search_term }}&page={{ page-1 }}" class="page-link">
                        <i class="fas fa-arrow-left"></i> Previous
                    </a>
                {% endif %}
                
                {% set start = [1, page-2]|max %}
                {% set end = [total_pages, page+2]|min %}
                
                {% if start > 1 %}
                    <a href="?year={{ year_id }}&grade={{ grade_id }}&section={{ section_id }}&search={{ search_term }}&page=1" class="page-link">1</a>
                    {% if start > 2 %}<span>...</span>{% endif %}
                {% endif %}
                
                {% for p in range(start, end+1) %}
                    {% if p == page %}
                        <span class="current-page">{{ p }}</span>
                    {% else %}
                        <a href="?year={{ year_id }}&grade={{ grade_id }}&section={{ section_id }}&search={{ search_term }}&page={{ p }}" class="page-link">{{ p }}</a>
                    {% endif %}
                {% endfor %}
                
                {% if end < total_pages %}
                    {% if end < total_pages - 1 %}<span>...</span>{% endif %}
                    <a href="?year={{ year_id }}&grade={{ grade_id }}&section={{ section_id }}&search={{ search_term }}&page={{ total_pages }}" class="page-link">{{ total_pages }}</a>
                {% endif %}
                
                {% if page < total_pages %}
                    <a href="?year={{ year_id }}&grade={{ grade_id }}&section={{ section_id }}&search={{ search_term }}&page={{ page+1 }}" class="page-link">
                        Next <i class="fas fa-arrow-right"></i>
                    </a>
                {% endif %}
            </div>
            {% endif %}
            
            {% else %}
            <div class="alert alert-danger">
                <h3>No Results Found</h3>
                <p>No student records match the selected filters.</p>
                <p>Please check that:</p>
                <ul>
                    <li>Students have been assigned to this section</li>
                    <li>The selected room teacher is correct</li>
                    <li>The semester selection is correct</li>
                </ul>
            </div>
            {% endif %}
            {% elif year_id and grade_id and not section_id %}
            <div style="text-align: center; margin: 20px 0;">
                <p style="color: #666;">Please select a section to view student data.</p>
            </div>
            {% endif %}
            
            <div style="margin-top: 20px; text-align: center;">
                <a href="/director/director_dashboard" class="btn btn-primary">
                    <i class="fas fa-arrow-left"></i> Back to Dashboard
                </a>
            </div>
        </div>
        
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script>
            $(document).ready(function() {
                // Auto-submit when grade changes to populate section dropdown
                $('#gradeSelect').change(function() {
                    var year = $('#yearSelect').val();
                    var grade = $(this).val();
                    
                    if (year && grade) {
                        $('#filterForm').submit();
                    } else if (grade) {
                        $('#filterForm').submit();
                    }
                });
                
                // Auto-submit when year changes
                $('#yearSelect').change(function() {
                    $('#filterForm').submit();
                });
            });
        </script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''',
    academic_years=academic_years,
    grades=grades,
    section_options=section_options,
    year_id=year_id,
    grade_id=grade_id,
    section_id=section_id,
    semester=semester,
    search_term=search_term,
    page=page,
    total_pages=total_pages,
    students=students,
    grade_name=grade_name,
    section_name=section_name,
    ethiopian_year=ethiopian_year,
    room_teacher_name=room_teacher_name,
    failed_count=failed_count,
    show_results=show_results
    )

def export_to_csv(conn, year_id, grade_id, section_id, search_term):
    """Export student roster to CSV"""
    cursor = conn.cursor(dictionary=True)
    
    # Determine subjects based on grade level
    if grade_id >= 11 and grade_id <= 12:
        subjects = ['Amh', 'Eng', 'Maths', 'GSc', 'SSc', 'Ctzp', 'IT', 'Arts', 'HPE', 'CTE']
    else:
        subjects = ['Amh', 'Eng', 'Maths', 'EnSc', 'Arts', 'HPE', 'Ethics']
    
    subject_count = len(subjects)
    
    f_selects = [f"s1.`{sub}` AS f_{sub}" for sub in subjects]
    s_selects = [f"s2.`{sub}` AS s_{sub}" for sub in subjects]
    
    query = f"""
        SELECT 
            e.student_RN as RN,
            e.studid, 
            s.fullname, 
            s.gender, 
            s.age,
            {', '.join(f_selects)},
            {', '.join(s_selects)}
        FROM enrollment e
        INNER JOIN student s ON e.student_RN = s.RN
        LEFT JOIN student_scores s1 ON s.RN = s1.student_RN AND s1.semester = '1' 
            AND s1.academic_year_id = e.academic_year_id 
            AND s1.grade_id = e.grade_id 
            AND s1.section_id = e.section_id
        LEFT JOIN student_scores s2 ON s.RN = s2.student_RN AND s2.semester = '2' 
            AND s2.academic_year_id = e.academic_year_id 
            AND s2.grade_id = e.grade_id 
            AND s2.section_id = e.section_id
        WHERE e.academic_year_id = %s 
          AND e.grade_id = %s
          AND e.section_id = %s
        ORDER BY CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(e.studid, '/', -2), '/', 1) AS UNSIGNED) ASC
    """
    params = [year_id, grade_id, section_id]
    
    if search_term:
        query = query.replace("WHERE", "WHERE (s.fullname LIKE %s OR e.studid LIKE %s) AND")
        search_param = f"%{search_term}%"
        params = [search_param, search_param] + params
    
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write CSV headers
    headers = ['RN', 'ID', 'Full Name', 'Gender', 'Age', 'Sem'] + subjects + ['Sum', 'Avg', 'Rank', 'Remark']
    writer.writerow(headers)
    
    for row in results:
        f_scores = [row.get(f'f_{sub}') for sub in subjects]
        s_scores = [row.get(f's_{sub}') for sub in subjects]
        
        f_sum = sum([s for s in f_scores if s is not None]) or 0
        s_sum = sum([s for s in s_scores if s is not None]) or 0
        f_avg = round(f_sum / subject_count, 2) if f_sum > 0 else None
        s_avg = round(s_sum / subject_count, 2) if s_sum > 0 else None
        
        a_scores = []
        a_sum = 0
        for i in range(subject_count):
            if f_scores[i] is not None and s_scores[i] is not None:
                avg_val = round((f_scores[i] + s_scores[i]) / 2, 2)
                a_scores.append(avg_val)
                a_sum += avg_val
            elif f_scores[i] is not None:
                a_scores.append(f_scores[i])
                a_sum += f_scores[i]
            elif s_scores[i] is not None:
                a_scores.append(s_scores[i])
                a_sum += s_scores[i]
            else:
                a_scores.append(None)
        
        a_avg = round(a_sum / subject_count, 2) if a_sum > 0 else None
        remark = 'Passed' if a_avg is not None and a_avg >= 50 else 'Failed'
        
        # First semester row
        row1 = [row['RN'], row['studid'], row['fullname'], row['gender'] or '', row['age'] or '', '1st']
        row1.extend([s if s is not None else 'NULL' for s in f_scores])
        row1.extend([f_sum if f_sum > 0 else 'NULL', f_avg if f_avg is not None else 'NULL', '', remark])
        writer.writerow(row1)
        
        # Second semester row
        row2 = ['', '', '', '', '', '2nd']
        row2.extend([s if s is not None else 'NULL' for s in s_scores])
        row2.extend([s_sum if s_sum > 0 else 'NULL', s_avg if s_avg is not None else 'NULL', '', ''])
        writer.writerow(row2)
        
        # Average row
        row3 = ['', '', '', '', '', 'Avg']
        row3.extend([s if s is not None else 'NULL' for s in a_scores])
        row3.extend([a_sum if a_sum > 0 else 'NULL', a_avg if a_avg is not None else 'NULL', '', ''])
        writer.writerow(row3)
    
    cursor.close()
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=student_roster.csv'
    return response