# ==============================================
# semester_and_average_analysis.py
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import math

director_semester_and_average_analysis = Blueprint('director_semester_and_average_analysis', __name__, url_prefix='/director')

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

def get_dropdown_options(cursor, table, id_col, name_col, where=""):
    options = {}
    sql = f"SELECT {id_col}, {name_col} FROM {table}"
    if where:
        sql += f" WHERE {where}"
    cursor.execute(sql)
    for row in cursor.fetchall():
        options[row[id_col]] = row[name_col]
    return options

def get_summary_analysis(cursor, academic_year_id):
    """Get subject-based summary for all grades with selected academic year"""
    summary = []
    
    # Get all grades from 5-12 (excluding kindergarten)
    cursor.execute("SELECT ID, level FROM grade WHERE ID BETWEEN 5 AND 12 ORDER BY ID")
    grades = cursor.fetchall()
    
    for grade in grades:
        grade_id = grade['ID']
        grade_name = grade['level']
        
        # Get all non-null sections for this grade
        cursor.execute("SELECT ID, sec_name FROM section WHERE grade_id = %s AND sec_name IS NOT NULL", (grade_id,))
        sections = cursor.fetchall()
        
        # Determine subjects based on grade level
        if grade_id >= 11 and grade_id <= 12:
            subjects = ['Amh', 'Eng', 'Maths', 'GSc', 'SSc', 'Ctzp', 'IT', 'Arts', 'HPE', 'CTE']
        else:
            subjects = ['Amh', 'Eng', 'Maths', 'EnSc', 'Arts', 'HPE', 'Ethics']
        
        grade_data = {
            'grade_id': grade_id,
            'grade_name': grade_name,
            'sections': [],
            'semester_1_totals': {},
            'semester_2_totals': {},
            'subject_totals': {}
        }
        
        # Initialize subject structures for all semesters
        for subject in subjects:
            grade_data['semester_1_totals'][subject] = {
                'registered': {'M': 0, 'F': 0, 'T': 0},
                'examined': {'M': 0, 'F': 0, 'T': 0},
                'lt50': {'M': 0, 'F': 0, 'T': 0},
                'gte50': {'M': 0, 'F': 0, 'T': 0},
                'gte75': {'M': 0, 'F': 0, 'T': 0},
                'gte85': {'M': 0, 'F': 0, 'T': 0}
            }
            
            grade_data['semester_2_totals'][subject] = {
                'registered': {'M': 0, 'F': 0, 'T': 0},
                'examined': {'M': 0, 'F': 0, 'T': 0},
                'lt50': {'M': 0, 'F': 0, 'T': 0},
                'gte50': {'M': 0, 'F': 0, 'T': 0},
                'gte75': {'M': 0, 'F': 0, 'T': 0},
                'gte85': {'M': 0, 'F': 0, 'T': 0}
            }
            
            grade_data['subject_totals'][subject] = {
                'registered': {'M': 0, 'F': 0, 'T': 0},
                'examined': {'M': 0, 'F': 0, 'T': 0},
                'lt50': {'M': 0, 'F': 0, 'T': 0},
                'gte50': {'M': 0, 'F': 0, 'T': 0},
                'gte75': {'M': 0, 'F': 0, 'T': 0},
                'gte85': {'M': 0, 'F': 0, 'T': 0}
            }
        
        for section in sections:
            section_id = section['ID']
            section_name = section['sec_name']
            
            # Process both semesters
            for sem in [1, 2]:
                # Get students for this section and semester
                students_query = """
                    SELECT s.RN, e.studid, s.fullname, s.gender, s.age, s.is_blind
                    FROM student s
                    JOIN enrollment e ON s.RN = e.student_RN 
                        AND e.academic_year_id = s.academic_year_id
                        AND e.grade_id = s.grade_id
                        AND e.section_id = s.section_id
                    JOIN student_scores ss ON s.RN = ss.student_RN
                    WHERE ss.academic_year_id = %s
                        AND ss.grade_id = %s
                        AND ss.section_id = %s
                        AND ss.semester = %s
                    ORDER BY s.fullname
                """
                cursor.execute(students_query, (academic_year_id, grade_id, section_id, str(sem)))
                students = cursor.fetchall()
                
                subject_analysis = {}
                for subject in subjects:
                    subject_analysis[subject] = {
                        'registered': {'M': 0, 'F': 0, 'T': 0},
                        'examined': {'M': 0, 'F': 0, 'T': 0},
                        'lt50': {'M': 0, 'F': 0, 'T': 0},
                        'gte50': {'M': 0, 'F': 0, 'T': 0},
                        'gte75': {'M': 0, 'F': 0, 'T': 0},
                        'gte85': {'M': 0, 'F': 0, 'T': 0}
                    }
                
                for student in students:
                    gender = student.get('gender')
                    if gender not in ['M', 'F']:
                        continue
                    
                    # Get student scores
                    cursor.execute("""
                        SELECT * FROM student_scores 
                        WHERE student_RN = %s
                        AND academic_year_id = %s
                        AND grade_id = %s
                        AND section_id = %s
                        AND semester = %s
                    """, (student['RN'], academic_year_id, grade_id, section_id, str(sem)))
                    scores = cursor.fetchone()
                    
                    if scores:
                        for subject in subjects:
                            subject_analysis[subject]['registered'][gender] += 1
                            subject_analysis[subject]['registered']['T'] += 1
                            
                            score = scores.get(subject)
                            if score is not None and score != '':
                                subject_analysis[subject]['examined'][gender] += 1
                                subject_analysis[subject]['examined']['T'] += 1
                                
                                if score < 50:
                                    subject_analysis[subject]['lt50'][gender] += 1
                                    subject_analysis[subject]['lt50']['T'] += 1
                                else:
                                    subject_analysis[subject]['gte50'][gender] += 1
                                    subject_analysis[subject]['gte50']['T'] += 1
                                    
                                    if score >= 75:
                                        subject_analysis[subject]['gte75'][gender] += 1
                                        subject_analysis[subject]['gte75']['T'] += 1
                                        
                                        if score >= 85:
                                            subject_analysis[subject]['gte85'][gender] += 1
                                            subject_analysis[subject]['gte85']['T'] += 1
                
                # Calculate percentages for each subject for this semester
                for subject in subjects:
                    for gender in ['M', 'F', 'T']:
                        examined = subject_analysis[subject]['examined'][gender]
                        
                        subject_analysis[subject]['lt50_pct'] = subject_analysis[subject].get('lt50_pct', {})
                        subject_analysis[subject]['gte50_pct'] = subject_analysis[subject].get('gte50_pct', {})
                        subject_analysis[subject]['gte75_pct'] = subject_analysis[subject].get('gte75_pct', {})
                        subject_analysis[subject]['gte85_pct'] = subject_analysis[subject].get('gte85_pct', {})
                        
                        subject_analysis[subject]['lt50_pct'][gender] = round((subject_analysis[subject]['lt50'][gender] / examined) * 100, 2) if examined > 0 else 0
                        subject_analysis[subject]['gte50_pct'][gender] = round((subject_analysis[subject]['gte50'][gender] / examined) * 100, 2) if examined > 0 else 0
                        subject_analysis[subject]['gte75_pct'][gender] = round((subject_analysis[subject]['gte75'][gender] / examined) * 100, 2) if examined > 0 else 0
                        subject_analysis[subject]['gte85_pct'][gender] = round((subject_analysis[subject]['gte85'][gender] / examined) * 100, 2) if examined > 0 else 0
                    
                    # Accumulate data for the semester totals
                    target_totals = grade_data['semester_1_totals'] if sem == 1 else grade_data['semester_2_totals']
                    for gender in ['M', 'F', 'T']:
                        target_totals[subject]['registered'][gender] += subject_analysis[subject]['registered'][gender]
                        target_totals[subject]['examined'][gender] += subject_analysis[subject]['examined'][gender]
                        target_totals[subject]['lt50'][gender] += subject_analysis[subject]['lt50'][gender]
                        target_totals[subject]['gte50'][gender] += subject_analysis[subject]['gte50'][gender]
                        target_totals[subject]['gte75'][gender] += subject_analysis[subject]['gte75'][gender]
                        target_totals[subject]['gte85'][gender] += subject_analysis[subject]['gte85'][gender]
                        
                        target_totals[subject]['lt50_pct'] = target_totals[subject].get('lt50_pct', {})
                        target_totals[subject]['gte50_pct'] = target_totals[subject].get('gte50_pct', {})
                        target_totals[subject]['gte75_pct'] = target_totals[subject].get('gte75_pct', {})
                        target_totals[subject]['gte85_pct'] = target_totals[subject].get('gte85_pct', {})
                        
                        target_totals[subject]['lt50_pct'][gender] = subject_analysis[subject]['lt50_pct'][gender]
                        target_totals[subject]['gte50_pct'][gender] = subject_analysis[subject]['gte50_pct'][gender]
                        target_totals[subject]['gte75_pct'][gender] = subject_analysis[subject]['gte75_pct'][gender]
                        target_totals[subject]['gte85_pct'][gender] = subject_analysis[subject]['gte85_pct'][gender]
                
                # Add to grade data
                grade_data['sections'].append({
                    'section_id': section_id,
                    'section_name': section_name,
                    'semester_' + str(sem): subject_analysis
                })
        
        # Calculate totals for the grade (average of both semesters) for Annual Average view
        for subject in subjects:
            for gender in ['M', 'F', 'T']:
                has_sem1 = grade_data['semester_1_totals'][subject]['examined'][gender] > 0
                has_sem2 = grade_data['semester_2_totals'][subject]['examined'][gender] > 0
                
                if has_sem1 and has_sem2:
                    grade_data['subject_totals'][subject]['registered'][gender] = (grade_data['semester_1_totals'][subject]['registered'][gender] + grade_data['semester_2_totals'][subject]['registered'][gender]) / 2
                    grade_data['subject_totals'][subject]['examined'][gender] = (grade_data['semester_1_totals'][subject]['examined'][gender] + grade_data['semester_2_totals'][subject]['examined'][gender]) / 2
                    grade_data['subject_totals'][subject]['lt50'][gender] = (grade_data['semester_1_totals'][subject]['lt50'][gender] + grade_data['semester_2_totals'][subject]['lt50'][gender]) / 2
                    grade_data['subject_totals'][subject]['gte50'][gender] = (grade_data['semester_1_totals'][subject]['gte50'][gender] + grade_data['semester_2_totals'][subject]['gte50'][gender]) / 2
                    grade_data['subject_totals'][subject]['gte75'][gender] = (grade_data['semester_1_totals'][subject]['gte75'][gender] + grade_data['semester_2_totals'][subject]['gte75'][gender]) / 2
                    grade_data['subject_totals'][subject]['gte85'][gender] = (grade_data['semester_1_totals'][subject]['gte85'][gender] + grade_data['semester_2_totals'][subject]['gte85'][gender]) / 2
                elif has_sem1 and not has_sem2:
                    grade_data['subject_totals'][subject]['registered'][gender] = grade_data['semester_1_totals'][subject]['registered'][gender]
                    grade_data['subject_totals'][subject]['examined'][gender] = 0
                    grade_data['subject_totals'][subject]['lt50'][gender] = 0
                    grade_data['subject_totals'][subject]['gte50'][gender] = 0
                    grade_data['subject_totals'][subject]['gte75'][gender] = 0
                    grade_data['subject_totals'][subject]['gte85'][gender] = 0
                elif not has_sem1 and has_sem2:
                    grade_data['subject_totals'][subject]['registered'][gender] = grade_data['semester_2_totals'][subject]['registered'][gender]
                    grade_data['subject_totals'][subject]['examined'][gender] = 0
                    grade_data['subject_totals'][subject]['lt50'][gender] = 0
                    grade_data['subject_totals'][subject]['gte50'][gender] = 0
                    grade_data['subject_totals'][subject]['gte75'][gender] = 0
                    grade_data['subject_totals'][subject]['gte85'][gender] = 0
                else:
                    grade_data['subject_totals'][subject]['registered'][gender] = 0
                    grade_data['subject_totals'][subject]['examined'][gender] = 0
                    grade_data['subject_totals'][subject]['lt50'][gender] = 0
                    grade_data['subject_totals'][subject]['gte50'][gender] = 0
                    grade_data['subject_totals'][subject]['gte75'][gender] = 0
                    grade_data['subject_totals'][subject]['gte85'][gender] = 0
        
        # Calculate percentages for grade totals
        for subject in subjects:
            for gender in ['M', 'F', 'T']:
                examined = grade_data['subject_totals'][subject]['examined'][gender]
                
                grade_data['subject_totals'][subject]['lt50_pct'] = grade_data['subject_totals'][subject].get('lt50_pct', {})
                grade_data['subject_totals'][subject]['gte50_pct'] = grade_data['subject_totals'][subject].get('gte50_pct', {})
                grade_data['subject_totals'][subject]['gte75_pct'] = grade_data['subject_totals'][subject].get('gte75_pct', {})
                grade_data['subject_totals'][subject]['gte85_pct'] = grade_data['subject_totals'][subject].get('gte85_pct', {})
                
                grade_data['subject_totals'][subject]['lt50_pct'][gender] = round((grade_data['subject_totals'][subject]['lt50'][gender] / examined) * 100, 2) if examined > 0 else 0
                grade_data['subject_totals'][subject]['gte50_pct'][gender] = round((grade_data['subject_totals'][subject]['gte50'][gender] / examined) * 100, 2) if examined > 0 else 0
                grade_data['subject_totals'][subject]['gte75_pct'][gender] = round((grade_data['subject_totals'][subject]['gte75'][gender] / examined) * 100, 2) if examined > 0 else 0
                grade_data['subject_totals'][subject]['gte85_pct'][gender] = round((grade_data['subject_totals'][subject]['gte85'][gender] / examined) * 100, 2) if examined > 0 else 0
        
        summary.append(grade_data)
    
    return summary

@director_semester_and_average_analysis.route('/semester_and_average_analysis')
@login_required
def semester_and_average_analysis_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get filter values
    academic_year_id = request.args.get('year', 0, type=int)
    view = request.args.get('view', 'average')
    
    # Get all academic years for dropdown
    year_options = get_dropdown_options(cursor, "academic_year", "ID", "ec_year")
    
    # Get Ethiopian year based on selection
    ethiopian_year = "Unknown"
    if academic_year_id > 0:
        cursor.execute("SELECT ec_year FROM academic_year WHERE ID = %s", (academic_year_id,))
        result = cursor.fetchone()
        if result:
            ethiopian_year = result['ec_year']
    else:
        cursor.execute("SELECT ec_year FROM academic_year WHERE is_active = 1 LIMIT 1")
        result = cursor.fetchone()
        if result:
            ethiopian_year = result['ec_year']
            # Set the academic_year_id to the active year for queries
            cursor.execute("SELECT ID FROM academic_year WHERE ec_year = %s", (ethiopian_year,))
            year_result = cursor.fetchone()
            if year_result:
                academic_year_id = year_result['ID']
    
    # Get summary analysis
    summary_analysis = []
    if academic_year_id > 0:
        summary_analysis = get_summary_analysis(cursor, academic_year_id)
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>School Performance Summary Analysis</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .report-header {
                text-align: center;
                margin-bottom: 30px;
            }
            .report-header h1 {
                margin-bottom: 5px;
                color: #2c3e50;
            }
            .report-header h2 {
                margin-top: 0;
                color: #555;
            }
            .filter-form {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                text-align: center;
            }
            .filter-form select, .filter-form button {
                padding: 10px 15px;
                margin: 0 5px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            .filter-form button {
                background-color: #4CAF50;
                color: white;
                border: none;
                cursor: pointer;
            }
            .filter-form button:hover {
                background-color: #45a049;
            }
            .grade-section {
                margin-bottom: 40px;
                page-break-after: always;
            }
            .grade-title {
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 15px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                font-size: 12px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .subject-row {
                background-color: #f9f9f9;
            }
            .average-row {
                background-color: #e6e6e6;
                font-weight: bold;
            }
            .print-button {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 20px 0;
                cursor: pointer;
                border-radius: 5px;
            }
            .view-buttons {
                text-align: center;
                margin: 20px 0;
            }
            .view-button {
                background-color: #2196F3;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 0 5px;
                cursor: pointer;
                border-radius: 5px;
            }
            .view-button.active {
                background-color: #0b7dda;
                font-weight: bold;
            }
            .back-button {
                background-color: #6c757d;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 20px 10px;
                cursor: pointer;
                border-radius: 5px;
            }
            .back-button:hover {
                background-color: #5a6268;
            }
            .current-year {
                background-color: #e8f4f8;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
                text-align: center;
            }
            @media print {
                .filter-form, .print-button, .view-buttons, .back-button {
                    display: none;
                }
                .grade-section {
                    page-break-after: always;
                }
                body {
                    background: white;
                    padding: 0;
                }
                .container {
                    box-shadow: none;
                    padding: 0;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="report-header">
                <h2>Melkakole First and Medium School</h2>
                <h2>Academic Year: {{ ethiopian_year }} E.C.</h2>
                <h3>Grades 5-12 Semester and Annual Average Performance Analysis</h3>
            </div>
            
            <!-- Academic Year Filter Form -->
            <div class="filter-form">
                <form method="GET" action="">
                    <label for="year">Select Academic Year: </label>
                    <select name="year" id="year" onchange="this.form.submit()">
                        <option value="">-- Select Academic Year --</option>
                        {% for id, year in year_options.items() %}
                            <option value="{{ id }}" {% if year_id == id %}selected{% endif %}>
                                {{ year }} E.C.
                            </option>
                        {% endfor %}
                    </select>
                    <button type="submit">View Report</button>
                    {% if year_id > 0 %}
                        <a href="/director/semester_and_average_analysis" style="text-decoration: none;">
                            <button type="button" style="background-color: #dc3545; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">Clear Filter</button>
                        </a>
                    {% endif %}
                </form>
            </div>
            
            {% if year_id > 0 %}
            <div class="current-year">
                <strong>Showing data for Academic Year: {{ ethiopian_year }} E.C.</strong>
            </div>
            {% endif %}
            
            <div class="view-buttons">
                <a href="?year={{ year_id }}&view=semester1" class="view-button {% if view == 'semester1' %}active{% endif %}">First Semester</a>
                <a href="?year={{ year_id }}&view=semester2" class="view-button {% if view == 'semester2' %}active{% endif %}">Second Semester</a>
                <a href="?year={{ year_id }}&view=average" class="view-button {% if view == 'average' %}active{% endif %}">Annual Average</a>
            </div>

            <button class="print-button" onclick="window.print()">Print Report</button>
            
            {% if not summary_analysis %}
            <div style="text-align: center; padding: 50px; color: #666;">
                <h3>No Data Available</h3>
                <p>Please select an academic year to view the performance analysis report.</p>
            </div>
            {% else %}
                {% for grade_data in summary_analysis %}
                <div class="grade-section">
                    <div class="grade-title">
                        <h2>Grade: {{ grade_data.grade_name }} - 
                            {% if view == 'semester1' %}First Semester
                            {% elif view == 'semester2' %}Second Semester
                            {% else %}Annual Average{% endif %}
                        </h2>
                    </div>
                    
                    <h3>Student Counts</h3>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead>
                                <tr>
                                    <th rowspan="2">Subject</th>
                                    <th colspan="3">Registered</th>
                                    <th colspan="3">Examined</th>
                                    <th colspan="3">&lt;50</th>
                                    <th colspan="3">≥50</th>
                                    <th colspan="3">≥75</th>
                                    <th colspan="3">≥85</th>
                                </tr>
                                <tr>
                                    <th>M</th><th>F</th><th>T</th>
                                    <th>M</th><th>F</th><th>T</th>
                                    <th>M</th><th>F</th><th>T</th>
                                    <th>M</th><th>F</th><th>T</th>
                                    <th>M</th><th>F</th><th>T</th>
                                    <th>M</th><th>F</th><th>T</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% set display_data = grade_data.semester_1_totals if view == 'semester1' else (grade_data.semester_2_totals if view == 'semester2' else grade_data.subject_totals) %}
                                {% set sum_registered = {'M': 0, 'F': 0, 'T': 0} %}
                                {% set sum_examined = {'M': 0, 'F': 0, 'T': 0} %}
                                {% set sum_lt50 = {'M': 0, 'F': 0, 'T': 0} %}
                                {% set sum_gte50 = {'M': 0, 'F': 0, 'T': 0} %}
                                {% set sum_gte75 = {'M': 0, 'F': 0, 'T': 0} %}
                                {% set sum_gte85 = {'M': 0, 'F': 0, 'T': 0} %}
                                
                                {% for subject, data in display_data.items() %}
                                <tr class="subject-row">
                                    <td>{{ subject }}</td>
                                    <td>{{ data.registered.M|round|int }}</td>
                                    <td>{{ data.registered.F|round|int }}</td>
                                    <td>{{ data.registered.T|round|int }}</td>
                                    <td>{{ data.examined.M|round|int }}</td>
                                    <td>{{ data.examined.F|round|int }}</td>
                                    <td>{{ data.examined.T|round|int }}</td>
                                    <td>{{ data.lt50.M|round|int }}</td>
                                    <td>{{ data.lt50.F|round|int }}</td>
                                    <td>{{ data.lt50.T|round|int }}</td>
                                    <td>{{ data.gte50.M|round|int }}</td>
                                    <td>{{ data.gte50.F|round|int }}</td>
                                    <td>{{ data.gte50.T|round|int }}</td>
                                    <td>{{ data.gte75.M|round|int }}</td>
                                    <td>{{ data.gte75.F|round|int }}</td>
                                    <td>{{ data.gte75.T|round|int }}</td>
                                    <td>{{ data.gte85.M|round|int }}</td>
                                    <td>{{ data.gte85.F|round|int }}</td>
                                    <td>{{ data.gte85.T|round|int }}</td>
                                </tr>
                                {% set _ = sum_registered.update({'M': sum_registered.M + (data.registered.M|round|int), 'F': sum_registered.F + (data.registered.F|round|int), 'T': sum_registered.T + (data.registered.T|round|int)}) %}
                                {% set _ = sum_examined.update({'M': sum_examined.M + (data.examined.M|round|int), 'F': sum_examined.F + (data.examined.F|round|int), 'T': sum_examined.T + (data.examined.T|round|int)}) %}
                                {% set _ = sum_lt50.update({'M': sum_lt50.M + (data.lt50.M|round|int), 'F': sum_lt50.F + (data.lt50.F|round|int), 'T': sum_lt50.T + (data.lt50.T|round|int)}) %}
                                {% set _ = sum_gte50.update({'M': sum_gte50.M + (data.gte50.M|round|int), 'F': sum_gte50.F + (data.gte50.F|round|int), 'T': sum_gte50.T + (data.gte50.T|round|int)}) %}
                                {% set _ = sum_gte75.update({'M': sum_gte75.M + (data.gte75.M|round|int), 'F': sum_gte75.F + (data.gte75.F|round|int), 'T': sum_gte75.T + (data.gte75.T|round|int)}) %}
                                {% set _ = sum_gte85.update({'M': sum_gte85.M + (data.gte85.M|round|int), 'F': sum_gte85.F + (data.gte85.F|round|int), 'T': sum_gte85.T + (data.gte85.T|round|int)}) %}
                                {% endfor %}
                                
                                {% set subject_count = display_data|length %}
                                {% set avg_registered = {'M': (sum_registered.M / subject_count)|round|int if subject_count > 0 else 0, 'F': (sum_registered.F / subject_count)|round|int if subject_count > 0 else 0, 'T': (sum_registered.T / subject_count)|round|int if subject_count > 0 else 0} %}
                                {% set avg_examined = {'M': (sum_examined.M / subject_count)|round|int if subject_count > 0 else 0, 'F': (sum_examined.F / subject_count)|round|int if subject_count > 0 else 0, 'T': (sum_examined.T / subject_count)|round|int if subject_count > 0 else 0} %}
                                {% set avg_lt50 = {'M': (sum_lt50.M / subject_count)|round|int if subject_count > 0 else 0, 'F': (sum_lt50.F / subject_count)|round|int if subject_count > 0 else 0, 'T': (sum_lt50.T / subject_count)|round|int if subject_count > 0 else 0} %}
                                {% set avg_gte50 = {'M': (sum_gte50.M / subject_count)|round|int if subject_count > 0 else 0, 'F': (sum_gte50.F / subject_count)|round|int if subject_count > 0 else 0, 'T': (sum_gte50.T / subject_count)|round|int if subject_count > 0 else 0} %}
                                {% set avg_gte75 = {'M': (sum_gte75.M / subject_count)|round|int if subject_count > 0 else 0, 'F': (sum_gte75.F / subject_count)|round|int if subject_count > 0 else 0, 'T': (sum_gte75.T / subject_count)|round|int if subject_count > 0 else 0} %}
                                {% set avg_gte85 = {'M': (sum_gte85.M / subject_count)|round|int if subject_count > 0 else 0, 'F': (sum_gte85.F / subject_count)|round|int if subject_count > 0 else 0, 'T': (sum_gte85.T / subject_count)|round|int if subject_count > 0 else 0} %}
                                
                                <tr class="average-row">
                                    <td><strong>Grade {{ grade_data.grade_name }} Average</strong></td>
                                    <td><strong>{{ avg_registered.M }}</strong></td>
                                    <td><strong>{{ avg_registered.F }}</strong></td>
                                    <td><strong>{{ avg_registered.T }}</strong></td>
                                    <td><strong>{{ avg_examined.M }}</strong></td>
                                    <td><strong>{{ avg_examined.F }}</strong></td>
                                    <td><strong>{{ avg_examined.T }}</strong></td>
                                    <td><strong>{{ avg_lt50.M }}</strong></td>
                                    <td><strong>{{ avg_lt50.F }}</strong></td>
                                    <td><strong>{{ avg_lt50.T }}</strong></td>
                                    <td><strong>{{ avg_gte50.M }}</strong></td>
                                    <td><strong>{{ avg_gte50.F }}</strong></td>
                                    <td><strong>{{ avg_gte50.T }}</strong></td>
                                    <td><strong>{{ avg_gte75.M }}</strong></td>
                                    <td><strong>{{ avg_gte75.F }}</strong></td>
                                    <td><strong>{{ avg_gte75.T }}</strong></td>
                                    <td><strong>{{ avg_gte85.M }}</strong></td>
                                    <td><strong>{{ avg_gte85.F }}</strong></td>
                                    <td><strong>{{ avg_gte85.T }}</strong></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                {% endfor %}
            {% endif %}
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/director/director_dashboard" class="back-button">
                    <i class="fas fa-arrow-left"></i> Back to Dashboard
                </a>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''',
    year_options=year_options,
    year_id=academic_year_id,
    ethiopian_year=ethiopian_year,
    view=view,
    summary_analysis=summary_analysis
    )