# ==============================================
# semester_analysis.py - COMPLETE CONVERSION
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import math
import re

director_semester_average_analysis = Blueprint('director_semester_average_analysis', __name__, url_prefix='/director')

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

def get_options(cursor, table, id_col, name_col, where=""):
    options = {}
    sql = f"SELECT {id_col}, {name_col} FROM {table}"
    if where:
        sql += f" WHERE {where}"
    cursor.execute(sql)
    for row in cursor.fetchall():
        options[row[id_col]] = row[name_col]
    return options

def calculate_scores(student_data, is_blind, grade_id):
    """Calculate total, average, and process scores for a student"""
    if grade_id >= 11 and grade_id <= 12:
        all_subjects = ['Amh', 'Eng', 'Maths', 'GSc', 'SSc', 'Ctzp', 'IT', 'Arts', 'HPE', 'CTE']
    else:
        all_subjects = ['Amh', 'Eng', 'Maths', 'EnSc', 'Arts', 'HPE', 'Ethics']
    
    if is_blind:
        if grade_id >= 11 and grade_id <= 12:
            subjects = ['Amh', 'Eng', 'Arts', 'HPE']
        else:
            subjects = ['Amh', 'Eng', 'Arts', 'EnSc', 'HPE', 'Ethics']
    else:
        subjects = all_subjects
    
    total = 0
    null_found = False
    valid_scores = 0
    modified_scores = {}
    
    for subject in subjects:
        score = student_data.get(subject)
        if score == 0:
            score = None
        modified_scores[subject] = score
        
        if score is None:
            null_found = True
        else:
            total += score
            valid_scores += 1
    
    if null_found or valid_scores == 0:
        return {
            'total': None,
            'average': None,
            'rank': None,
            'subjects': subjects,
            'modified_scores': modified_scores
        }
    else:
        average = total / len(subjects)
        return {
            'total': total,
            'average': round(average, 2),
            'rank': None,
            'subjects': subjects,
            'modified_scores': modified_scores
        }

def get_room_teacher(cursor, section_id):
    teacher = {'name': 'Not Assigned', 'ID': 0}
    
    # METHOD 1: Direct section-teacher relationship
    cursor.execute("""
        SELECT t.ID, t.name 
        FROM section s
        INNER JOIN teacher t ON s.teacher_id = t.ID
        WHERE s.ID = %s
    """, (section_id,))
    result = cursor.fetchone()
    if result:
        teacher = result
    else:
        # METHOD 2: Fallback to assignment table
        cursor.execute("""
            SELECT t.ID, t.name 
            FROM teacher_assignment ta
            INNER JOIN teacher t ON ta.teacher_id = t.ID
            WHERE ta.section_id = %s AND ta.is_room_teacher = 1
            LIMIT 1
        """, (section_id,))
        result = cursor.fetchone()
        if result:
            teacher = result
    
    # SPECIAL CASE
    if section_id == 67:
        teacher = {'name': 'Meseret Wodaj', 'ID': 0}
    
    return teacher

@director_semester_average_analysis.route('/semester_average_analysis')
@login_required
def semester_average_analysis_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get filter values
    academic_year_id = request.args.get('year', 0, type=int)
    grade_id = request.args.get('grade', 0, type=int)
    section_id = request.args.get('section', 0, type=int)
    semester = request.args.get('semester', '1')
    
    # Load dropdown data
    year_options = get_options(cursor, "academic_year", "ID", "year")
    grade_options = get_options(cursor, "grade", "ID", "level")
    
    # Get sections for selected grade
    section_options = {}
    if grade_id:
        section_options = get_options(cursor, "section", "ID", "sec_name", f"grade_id = {grade_id}")
    
    # Get room teacher
    room_teacher = {'name': 'Not Assigned', 'ID': 0}
    if section_id:
        room_teacher = get_room_teacher(cursor, section_id)
    
    # Get Ethiopian year
    ethiopian_year = "Unknown"
    if academic_year_id:
        cursor.execute("SELECT ec_year FROM academic_year WHERE ID = %s", (academic_year_id,))
        result = cursor.fetchone()
        if result:
            ethiopian_year = result['ec_year']
    else:
        cursor.execute("SELECT ec_year FROM academic_year WHERE is_active = 1 LIMIT 1")
        result = cursor.fetchone()
        if result:
            ethiopian_year = result['ec_year']
    
    # Initialize variables
    students = []
    analysis = []
    show_analysis = False
    gender_totals = {'M': 0, 'F': 0}
    first_student_grade = ''
    first_student_section = ''
    
    # Define subjects
    if grade_id >= 11 and grade_id <= 12:
        subjects = ['Amh', 'Eng', 'Maths', 'GSc', 'SSc', 'Ctzp', 'IT', 'Arts', 'HPE', 'CTE']
    else:
        subjects = ['Amh', 'Eng', 'Maths', 'EnSc', 'Arts', 'HPE', 'Ethics']
    
    # Fetch students if all filters are set
    if academic_year_id and grade_id and section_id:
        # Build subject columns
        if grade_id >= 11 and grade_id <= 12:
            subject_columns = "ss.Amh, ss.Eng, ss.Maths, ss.GSc, ss.SSc, ss.Ctzp, ss.IT, ss.Arts, ss.HPE, ss.CTE"
        else:
            subject_columns = "ss.Amh, ss.Eng, ss.Maths, ss.EnSc, ss.Arts, ss.HPE, ss.Ethics"
        
        query = f"""
            SELECT 
                s.RN, 
                e.studid, 
                s.fullname, 
                s.gender, 
                s.age, 
                s.is_blind,
                g.level AS grade, 
                sec.sec_name AS section, 
                t.name AS teacher,
                ay.year AS academic_year,
                {subject_columns}
            FROM student s
            JOIN enrollment e ON s.RN = e.student_RN 
                AND e.academic_year_id = s.academic_year_id
                AND e.grade_id = s.grade_id
                AND e.section_id = s.section_id
            JOIN student_scores ss ON s.RN = ss.student_RN
            JOIN grade g ON ss.grade_id = g.ID
            JOIN section sec ON ss.section_id = sec.ID
            JOIN teacher t ON ss.teacher_id = t.ID
            JOIN academic_year ay ON ss.academic_year_id = ay.ID
            WHERE ss.academic_year_id = %s
              AND ss.grade_id = %s
              AND ss.section_id = %s
              AND ss.semester = %s
            ORDER BY CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(e.studid, '/', -2), '/', 1) AS UNSIGNED) ASC
        """
        
        cursor.execute(query, (academic_year_id, grade_id, section_id, semester))
        results = cursor.fetchall()
        
        for row in results:
            is_blind = row['is_blind'] == 1
            scores = calculate_scores(row, is_blind, grade_id)
            student_data = dict(row)
            student_data.update(scores)
            students.append(student_data)
            
            # Store first student's grade and section for display
            if not first_student_grade:
                first_student_grade = row.get('grade', '')
                first_student_section = row.get('section', '')
            
            # Count gender totals
            gender = row.get('gender')
            if gender in gender_totals:
                gender_totals[gender] += 1
        
        # Calculate ranks
        if students:
            rankable_students = [s for s in students if s.get('total') is not None]
            rankable_students.sort(key=lambda x: x.get('total', 0), reverse=True)
            
            rank = 1
            for student in rankable_students:
                student['rank'] = rank
                rank += 1
            
            for student in students:
                student['rank'] = None
                for ranked in rankable_students:
                    if student['RN'] == ranked['RN']:
                        student['rank'] = ranked['rank']
                        break
            
            show_analysis = True
    
    # Perform analysis if we have students
    if show_analysis:
        # Analyze each subject
        for subject in subjects:
            subject_data = {
                'subject': subject,
                'registered': {'M': 0, 'F': 0, 'T': 0},
                'examined': {'M': 0, 'F': 0, 'T': 0},
                'lt50': {'M': 0, 'F': 0, 'T': 0},
                'gte50': {'M': 0, 'F': 0, 'T': 0},
                'gte75': {'M': 0, 'F': 0, 'T': 0},
                'gte85': {'M': 0, 'F': 0, 'T': 0},
                'lt50_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte50_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte75_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte85_pct': {'M': 0, 'F': 0, 'T': 0}
            }
            
            for student in students:
                gender = student.get('gender')
                if gender not in ['M', 'F']:
                    continue
                
                subject_data['registered'][gender] += 1
                subject_data['registered']['T'] += 1
                
                modified_scores = student.get('modified_scores', {})
                if subject in modified_scores and modified_scores[subject] is not None:
                    score = modified_scores[subject]
                    subject_data['examined'][gender] += 1
                    subject_data['examined']['T'] += 1
                    
                    if score < 50:
                        subject_data['lt50'][gender] += 1
                        subject_data['lt50']['T'] += 1
                    else:
                        subject_data['gte50'][gender] += 1
                        subject_data['gte50']['T'] += 1
                        
                        if score >= 75:
                            subject_data['gte75'][gender] += 1
                            subject_data['gte75']['T'] += 1
                            
                            if score >= 85:
                                subject_data['gte85'][gender] += 1
                                subject_data['gte85']['T'] += 1
            
            # Calculate percentages
            for gender in ['M', 'F', 'T']:
                examined = subject_data['examined'][gender]
                subject_data['lt50_pct'][gender] = round((subject_data['lt50'][gender] / examined * 100), 2) if examined > 0 else 0
                subject_data['gte50_pct'][gender] = round((subject_data['gte50'][gender] / examined * 100), 2) if examined > 0 else 0
                subject_data['gte75_pct'][gender] = round((subject_data['gte75'][gender] / examined * 100), 2) if examined > 0 else 0
                subject_data['gte85_pct'][gender] = round((subject_data['gte85'][gender] / examined * 100), 2) if examined > 0 else 0
            
            analysis.append(subject_data)
        
        # Calculate averages
        averages = {
            'subject': 'Average',
            'registered': {'M': 0, 'F': 0, 'T': 0},
            'examined': {'M': 0, 'F': 0, 'T': 0},
            'lt50': {'M': 0, 'F': 0, 'T': 0},
            'gte50': {'M': 0, 'F': 0, 'T': 0},
            'gte75': {'M': 0, 'F': 0, 'T': 0},
            'gte85': {'M': 0, 'F': 0, 'T': 0},
            'lt50_pct': {'M': 0, 'F': 0, 'T': 0},
            'gte50_pct': {'M': 0, 'F': 0, 'T': 0},
            'gte75_pct': {'M': 0, 'F': 0, 'T': 0},
            'gte85_pct': {'M': 0, 'F': 0, 'T': 0}
        }
        
        for item in analysis:
            for gender in ['M', 'F', 'T']:
                averages['registered'][gender] += item['registered'][gender]
                averages['examined'][gender] += item['examined'][gender]
                averages['lt50'][gender] += item['lt50'][gender]
                averages['gte50'][gender] += item['gte50'][gender]
                averages['gte75'][gender] += item['gte75'][gender]
                averages['gte85'][gender] += item['gte85'][gender]
        
        subject_count = len(analysis)
        for gender in ['M', 'F', 'T']:
            averages['registered'][gender] = round(averages['registered'][gender] / subject_count, 1)
            averages['examined'][gender] = round(averages['examined'][gender] / subject_count, 1)
            averages['lt50'][gender] = round(averages['lt50'][gender] / subject_count, 1)
            averages['gte50'][gender] = round(averages['gte50'][gender] / subject_count, 1)
            averages['gte75'][gender] = round(averages['gte75'][gender] / subject_count, 1)
            averages['gte85'][gender] = round(averages['gte85'][gender] / subject_count, 1)
            
            examined = averages['examined'][gender]
            averages['lt50_pct'][gender] = round((averages['lt50'][gender] / examined * 100), 2) if examined > 0 else 0
            averages['gte50_pct'][gender] = round((averages['gte50'][gender] / examined * 100), 2) if examined > 0 else 0
            averages['gte75_pct'][gender] = round((averages['gte75'][gender] / examined * 100), 2) if examined > 0 else 0
            averages['gte85_pct'][gender] = round((averages['gte85'][gender] / examined * 100), 2) if examined > 0 else 0
        
        analysis.append(averages)
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Subject Based Scores Analysis</title>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
        <script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.js"></script>
        <script type="text/javascript" src="https://cdn.datatables.net/buttons/2.2.2/js/dataTables.buttons.min.js"></script>
        <script type="text/javascript" src="https://cdn.datatables.net/buttons/2.2.2/js/buttons.html5.min.js"></script>
        <script type="text/javascript" src="https://cdn.datatables.net/buttons/2.2.2/js/buttons.print.min.js"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f8fafc;
                color: #334155;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            .alert {
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 6px;
                text-align: center;
            }
            .alert-danger { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
            .alert-info { background-color: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc; }
            .alert-warning { background-color: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
            .search-form {
                background: white;
                padding: 1.75rem;
                border-radius: 0.75rem;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
                margin-bottom: 2rem;
                border: 1px solid #e2e8f0;
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
                color: #4a5568;
                font-size: 0.9375rem;
            }
            .form-control {
                width: 100%;
                padding: 0.625rem 0.875rem;
                border: 1px solid #e2e8f0;
                border-radius: 0.5rem;
                font-size: 0.9375rem;
            }
            .form-control:focus {
                outline: none;
                border-color: #7c3aed;
                box-shadow: 0 0 0 3px rgba(124,58,237,0.1);
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
            }
            .btn-primary { background-color: #7c3aed; color: white; }
            .btn-primary:hover { background-color: #6d28d9; transform: translateY(-1px); }
            .btn-danger { background-color: #dc3545; color: white; }
            .btn-danger:hover { background-color: #c82333; transform: translateY(-1px); }
            .form-actions {
                display: flex;
                gap: 0.75rem;
                margin-top: 1rem;
            }
            .teacher-selection {
                background-color: #e9f7ef;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 15px;
                text-align: center;
            }
            .teacher-selection strong { color: #28a745; }
            .results-container {
                background: white;
                border-radius: 0.75rem;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
                padding: 1.75rem;
                margin-bottom: 2rem;
                border: 1px solid #e2e8f0;
            }
            .header-info {
                text-align: center;
                margin-bottom: 20px;
            }
            .header-info h3 { margin-bottom: 5px; color: #2c3e50; }
            .header-info h4 {
                margin-top: 0;
                color: #4a5568;
                font-weight: normal;
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 15px;
            }
            .page-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 2rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid #e2e8f0;
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
            #analysisTable {
                width: 100%;
                border-collapse: collapse;
                font-size: 0.85em;
            }
            #analysisTable thead tr {
                background-color: #4a6fa5;
                color: #ffffff;
                text-align: center;
            }
            #analysisTable th, #analysisTable td {
                padding: 8px 10px;
                border: 1px solid #ddd;
                text-align: center;
            }
            #analysisTable tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
            #analysisTable tbody tr:hover { background-color: #f1f1f1; }
            @media screen and (max-width: 768px) {
                #analysisTable { font-size: 0.8em; }
                #analysisTable th, #analysisTable td { padding: 6px 8px; }
            }
            .dt-center { text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="page-header">
                <h1><i class="fas fa-chart-bar"></i> Subject Based Scores Analysis</h1>
                <a href="/director/view_student_scores" class="btn btn-primary">
                    <i class="fas fa-arrow-left"></i> Back to Scores
                </a>
            </div>

            {% if not (year_id and grade_id and section_id) %}
            <div class="search-form">
                <h2><i class="fas fa-filter"></i> Filter Students</h2>
                <form method="GET">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Academic Year</label>
                            <select name="year" class="form-control" required onchange="this.form.submit()">
                                <option value="">-- Select --</option>
                                {% for id, year in year_options.items() %}
                                    <option value="{{ id }}" {% if year_id == id %}selected{% endif %}>{{ year }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Grade</label>
                            <select name="grade" class="form-control" required onchange="this.form.submit()">
                                <option value="">-- Select --</option>
                                {% for id, grade in grade_options.items() %}
                                    <option value="{{ id }}" {% if grade_id == id %}selected{% endif %}>{{ grade }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Section</label>
                            <select name="section" class="form-control" required>
                                <option value="">-- Select --</option>
                                {% for id, section in section_options.items() %}
                                    <option value="{{ id }}" {% if section_id == id %}selected{% endif %}>{{ section }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    
                    {% if year_id and grade_id and section_id %}
                    <div class="teacher-selection">
                        <p>Selected Room Teacher: <strong>{{ room_teacher.name }}</strong></p>
                    </div>
                    {% endif %}
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Semester</label>
                            <select name="semester" class="form-control" required>
                                <option value="1" {% if semester == '1' %}selected{% endif %}>First Semester</option>
                                <option value="2" {% if semester == '2' %}selected{% endif %}>Second Semester</option>
                                <option value="annual" {% if semester == 'annual' %}selected{% endif %}>Annual Average</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-search"></i> Search
                        </button>
                        <a href="/director/semester_analysis" class="btn btn-danger">
                            <i class="fas fa-times"></i> Clear
                        </a>
                    </div>
                </form>
            </div>
            {% endif %}

            {% if show_analysis %}
            <div class="results-container">
                <div class="header-info">
                    <h3>Student Performance Analysis Report (Subject Based)</h3>
                    <h4>
                        <span>Academic Year: <b><u>{{ ethiopian_year }}</u></b></span>
                        <span>Grade: <b><u>{{ first_student_grade }}</u></b></span>
                        <span>Section: <b><u>{{ first_student_section }}</u></b></span>
                        <span>Teacher: <b><u>{{ room_teacher.name }}</u></b></span>
                        <span>Semester: <b><u>{{ 'First' if semester == '1' else 'Second' }}</u></b></span>
                        <span>Total Students: <b><u>{{ gender_totals.M + gender_totals.F }} (M:{{ gender_totals.M }}, F:{{ gender_totals.F }})</u></b></span>
                    </h4>
                </div>
                
                <table id="analysisTable" class="display nowrap" style="width:100%">
                    <thead>
                        <tr>
                            <th rowspan="2">Subject</th>
                            <th colspan="3">Registered</th>
                            <th colspan="3">Examined</th>
                            <th colspan="6">Score &lt; 50</th>
                            <th colspan="6">Score ≥ 50</th>
                            <th colspan="6">Score ≥ 75</th>
                            <th colspan="6">Score ≥ 85</th>
                        </tr>
                        <tr>
                            <th>M</th><th>F</th><th>T</th>
                            <th>M</th><th>F</th><th>T</th>
                            <th>M</th><th>F</th><th>T</th><th>M%</th><th>F%</th><th>T%</th>
                            <th>M</th><th>F</th><th>T</th><th>M%</th><th>F%</th><th>T%</th>
                            <th>M</th><th>F</th><th>T</th><th>M%</th><th>F%</th><th>T%</th>
                            <th>M</th><th>F</th><th>T</th><th>M%</th><th>F%</th><th>T%</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in analysis %}
                        <tr {% if item.subject == 'Average' %}style="font-weight: bold; background-color: #e6f3ff;"{% endif %}>
                            <td>{{ item.subject }}</td>
                            <!-- Registered -->
                            <td>{{ item.registered.M }}</td>
                            <td>{{ item.registered.F }}</td>
                            <td>{{ item.registered.T }}</td>
                            <!-- Examined -->
                            <td>{{ item.examined.M }}</td>
                            <td>{{ item.examined.F }}</td>
                            <td>{{ item.examined.T }}</td>
                            <!-- Score < 50 -->
                            <td>{{ item.lt50.M }}</td>
                            <td>{{ item.lt50.F }}</td>
                            <td>{{ item.lt50.T }}</td>
                            <td>{{ item.lt50_pct.M }}%</td>
                            <td>{{ item.lt50_pct.F }}%</td>
                            <td>{{ item.lt50_pct.T }}%</td>
                            <!-- Score ≥ 50 -->
                            <td>{{ item.gte50.M }}</td>
                            <td>{{ item.gte50.F }}</td>
                            <td>{{ item.gte50.T }}</td>
                            <td>{{ item.gte50_pct.M }}%</td>
                            <td>{{ item.gte50_pct.F }}%</td>
                            <td>{{ item.gte50_pct.T }}%</td>
                            <!-- Score ≥ 75 -->
                            <td>{{ item.gte75.M }}</td>
                            <td>{{ item.gte75.F }}</td>
                            <td>{{ item.gte75.T }}</td>
                            <td>{{ item.gte75_pct.M }}%</td>
                            <td>{{ item.gte75_pct.F }}%</td>
                            <td>{{ item.gte75_pct.T }}%</td>
                            <!-- Score ≥ 85 -->
                            <td>{{ item.gte85.M }}</td>
                            <td>{{ item.gte85.F }}</td>
                            <td>{{ item.gte85.T }}</td>
                            <td>{{ item.gte85_pct.M }}%</td>
                            <td>{{ item.gte85_pct.F }}%</td>
                            <td>{{ item.gte85_pct.T }}%</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <script>
                $(document).ready(function() {
                    $('#analysisTable').DataTable({
                        dom: 'Blfrtip',
                        buttons: ['copy', 'csv', 'excel', 'print'],
                        scrollX: true,
                        pageLength: 10,
                        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
                        columnDefs: [
                            { targets: [0], width: '120px' },
                            { targets: '_all', className: 'dt-center' }
                        ],
                        order: []
                    });
                });
            </script>
            {% elif year_id and grade_id and section_id %}
            <div class="alert alert-warning">
                <h3>No Data Found</h3>
                <p>No student records match the selected filters.</p>
                <p>Please check that scores have been entered for this section.</p>
            </div>
            {% endif %}
            
            <div style="margin-top: 20px; text-align: center;">
                <a href="/director/director_dashboard" class="btn btn-primary">
                    <i class="fas fa-arrow-left"></i> Back to Dashboard
                </a>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''',
    year_options=year_options,
    grade_options=grade_options,
    section_options=section_options,
    year_id=academic_year_id,
    grade_id=grade_id,
    section_id=section_id,
    semester=semester,
    analysis=analysis,
    show_analysis=show_analysis,
    room_teacher=room_teacher,
    ethiopian_year=ethiopian_year,
    gender_totals=gender_totals,
    first_student_grade=first_student_grade,
    first_student_section=first_student_section
    )