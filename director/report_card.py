# ==============================================
# report_card.py - FIXED TEMPLATE
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import math

director_report_card = Blueprint('director_report_card', __name__, url_prefix='/director')

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

@director_report_card.route('/report_card')
@login_required
def report_card_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get the active academic year from database
    ethiopian_year = "Unknown"
    cursor.execute("SELECT ec_year FROM academic_year WHERE is_active = 1 LIMIT 1")
    result = cursor.fetchone()
    if result:
        ethiopian_year = result['ec_year']
    
    # Get student ID from query parameter
    student_id = request.args.get('student_id', '')
    search_term = request.args.get('search', '')
    
    # Fetch all students for dropdown (excluding KG students)
    all_students_query = """
        SELECT s.RN, e.studid, s.fullname, s.gender, s.age, g.level, g.id as grade_id, 
               sec.sec_name, ay.ec_year as year, s.academic_year_id
        FROM student s
        INNER JOIN enrollment e ON s.RN = e.student_RN 
        INNER JOIN grade g ON s.grade_id = g.id
        INNER JOIN section sec ON s.section_id = sec.id
        INNER JOIN academic_year ay ON s.academic_year_id = ay.id
        WHERE g.level NOT LIKE '%KG%' 
        AND g.level NOT LIKE '%Kindergarten%'
    """
    params = []
    
    if search_term:
        all_students_query += " AND (e.studid LIKE %s OR s.fullname LIKE %s)"
        search_param = f"%{search_term}%"
        params = [search_param, search_param]
    
    all_students_query += " ORDER BY g.level, sec.sec_name, e.studid ASC"
    
    cursor.execute(all_students_query, tuple(params) if params else None)
    all_students = cursor.fetchall()
    
    # Initialize variables
    student_data = {}
    academic_info = {'academic_year': '', 'grade': '', 'section': ''}
    student_ranks = {'f_avg_rank': '--', 's_avg_rank': '--', 'a_avg_rank': '--'}
    scores = {'1': {}, '2': {}}
    subjects = []
    subject_labels = {}
    semester_totals = {'1': 0, '2': 0}
    semester_averages = {'1': 0, '2': 0}
    annual_averages = {}
    annual_totals = 0
    overall_annual_avg = None
    remark = ''
    
    if student_id:
        # Fetch specific student data
        query = """
            SELECT s.RN, e.studid, s.fullname, s.gender, s.age, g.level, g.id as grade_id, 
                   sec.sec_name, ay.ec_year as year, s.academic_year_id
            FROM student s
            LEFT JOIN enrollment e ON s.RN = e.student_RN 
            LEFT JOIN grade g ON s.grade_id = g.id
            LEFT JOIN section sec ON s.section_id = sec.id
            LEFT JOIN academic_year ay ON s.academic_year_id = ay.id
            WHERE e.studid = %s
        """
        cursor.execute(query, (student_id,))
        student_data = cursor.fetchone()
        
        if student_data:
            # Get the actual academic year
            academic_info['academic_year'] = student_data.get('year') or ethiopian_year
            academic_info['grade'] = student_data.get('level') or 'N/A'
            academic_info['section'] = student_data.get('sec_name') or 'N/A'
            
            grade_id = student_data.get('grade_id') or 0
            section_id = 0
            
            if student_data.get('RN'):
                cursor.execute("SELECT section_id FROM student WHERE RN = %s", (student_data['RN'],))
                section_result = cursor.fetchone()
                if section_result:
                    section_id = section_result['section_id']
            
            # Calculate ranks for all students in the same grade and section
            if grade_id and section_id:
                rank_query = """
                    SELECT s.RN,
                          AVG(CASE WHEN ss.semester = 1 THEN (ss.Amh + ss.Eng + ss.Maths + ss.EnSc + ss.Arts + ss.HPE + ss.Ethics) END) as f_avg,
                          AVG(CASE WHEN ss.semester = 2 THEN (ss.Amh + ss.Eng + ss.Maths + ss.EnSc + ss.Arts + ss.HPE + ss.Ethics) END) as s_avg,
                          (IFNULL(AVG(CASE WHEN ss.semester = 1 THEN (ss.Amh + ss.Eng + ss.Maths + ss.EnSc + ss.Arts + ss.HPE + ss.Ethics) END), 0) +
                           IFNULL(AVG(CASE WHEN ss.semester = 2 THEN (ss.Amh + ss.Eng + ss.Maths + ss.EnSc + ss.Arts + ss.HPE + ss.Ethics) END), 0)) / 2 as a_avg
                    FROM student s
                    LEFT JOIN student_scores ss ON s.RN = ss.student_RN
                    WHERE s.grade_id = %s AND s.section_id = %s
                    GROUP BY s.RN
                """
                cursor.execute(rank_query, (grade_id, section_id))
                rank_data = cursor.fetchall()
                current_rn = student_data['RN']
                
                if rank_data:
                    # Sort by first semester average
                    f_rank_data = sorted(rank_data, key=lambda x: x.get('f_avg') or 0, reverse=True)
                    for idx, student in enumerate(f_rank_data, 1):
                        if student['RN'] == current_rn:
                            student_ranks['f_avg_rank'] = idx
                            break
                    
                    # Sort by second semester average
                    s_rank_data = sorted(rank_data, key=lambda x: x.get('s_avg') or 0, reverse=True)
                    for idx, student in enumerate(s_rank_data, 1):
                        if student['RN'] == current_rn:
                            student_ranks['s_avg_rank'] = idx
                            break
                    
                    # Sort by annual average
                    a_rank_data = sorted(rank_data, key=lambda x: x.get('a_avg') or 0, reverse=True)
                    for idx, student in enumerate(a_rank_data, 1):
                        if student['RN'] == current_rn:
                            student_ranks['a_avg_rank'] = idx
                            break
            
            # Fetch scores for the student
            if student_data.get('RN'):
                cursor.execute("""
                    SELECT semester, Amh, Eng, Maths, EnSc, Arts, HPE, Ethics,
                           GSc, SSc, Ctzp, IT, CTE
                    FROM student_scores
                    WHERE student_RN = %s
                    ORDER BY semester
                """, (student_data['RN'],))
                scores_results = cursor.fetchall()
                
                for row in scores_results:
                    scores[str(row['semester'])] = row
            
            # Determine subjects based on grade_id
            grade_id = int(student_data.get('grade_id') or 0)
            
            if grade_id >= 11 and grade_id <= 12:
                subjects = ['Amh', 'Eng', 'Maths', 'GSc', 'SSc', 'Ctzp', 'IT', 'Arts', 'HPE', 'CTE']
                subject_labels = {s: s for s in subjects}
            else:
                subjects = ['Amh', 'Eng', 'Maths', 'EnSc', 'Arts', 'HPE', 'Ethics']
                subject_labels = {s: s for s in subjects}
            
            subject_count = len(subjects)
            
            # Calculate semester totals and averages
            for sem in ['1', '2']:
                if scores.get(sem):
                    total = 0
                    count = 0
                    for subject in subjects:
                        score = scores[sem].get(subject)
                        if score is not None and score != 0:
                            total += score
                            count += 1
                    semester_totals[sem] = total if count > 0 else None
                    semester_averages[sem] = round(total / count, 1) if count > 0 else None
                else:
                    semester_totals[sem] = None
                    semester_averages[sem] = None
            
            # Calculate annual averages (average of both semesters for each subject)
            annual_totals = 0
            valid_subject_count = 0
            
            for subject in subjects:
                sem1_score = scores.get('1', {}).get(subject)
                sem2_score = scores.get('2', {}).get(subject)
                has_sem1 = sem1_score is not None and sem1_score != 0
                has_sem2 = sem2_score is not None and sem2_score != 0
                
                if has_sem1 and has_sem2:
                    annual_averages[subject] = round((sem1_score + sem2_score) / 2, 1)
                    annual_totals += annual_averages[subject]
                    valid_subject_count += 1
                else:
                    annual_averages[subject] = None
            
            # Calculate overall annual average
            overall_annual_avg = round(annual_totals / valid_subject_count, 1) if valid_subject_count > 0 else None
            
            # Calculate overall totals for display (sum of subject averages)
            annual_total_display = annual_totals if annual_totals > 0 else None
            
            # Determine pass/fail status
            if overall_annual_avg is not None:
                remark = 'Passed' if overall_annual_avg >= 50 else 'Failed'
            else:
                remark = 'Incomplete'
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Melkakole School - Report Card Generator</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="{{ url_for('static', filename='css/report_card.css') }}">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="school-name">Melkakole First and Medium School</div>
                <div class="report-title">Students Report Card</div>
                <div class="academic-info">
                    Academic Year: <b><u>{{ academic_info.academic_year or ethiopian_year }}</u></b>
                    <span>Grade: {{ academic_info.grade }}</span>
                    <span>Section: {{ academic_info.section }}</span>
                </div>
            </div>

            <div class="student-selector">
                <h3>Search Student to Generate Report</h3>
                
                <!-- Search Form -->
                <form method="GET" class="search-container">
                    <input type="text" name="search" class="search-input" placeholder="Search by ID or Name..." value="{{ search_term }}">
                    <button type="submit">
                        <i class="fas fa-search"></i> Search Student
                    </button>
                    {% if search_term %}
                        <a href="/director/report_card" style="text-decoration: none;">
                            <button type="button" class="clear-btn">Clear Search</button>
                        </a>
                    {% endif %}
                </form>
                
                <!-- Student Selection Dropdown -->
                <form method="GET">
                    <div class="selector-container">
                        <select name="student_id" required>
                            <option value="">-- Select a student --</option>
                            {% for student in all_students %}
                                {% set gender_display = 'Male' if student.gender == 'M' else 'Female' %}
                                <option value="{{ student.studid }}" {% if student_id == student.studid %}selected{% endif %}>
                                    {{ student.studid }} - {{ student.fullname }} ({{ gender_display }}, Grade {{ student.level }}, Section {{ student.sec_name }})
                                </option>
                            {% endfor %}
                        </select>
                        <button type="submit">Generate Report</button>
                    </div>
                </form>
                
                {% if search_term %}
                    <div class="current-selection">
                        <strong>Search results for:</strong> "{{ search_term }}" - Found {{ all_students|length }} student(s)
                    </div>
                {% endif %}
            </div>

            <div class="report-content">
                <div id="reportData">
                    {% if student_data %}
                        {% set gender_display = 'Male' if student_data.gender == 'M' else 'Female' %}
                        {% set conduct = 'Good' if remark == 'Passed' else ('Poor' if remark == 'Failed' else 'Incomplete') %}
                        <div class="student-info">
                            <div class="info-grid">
                                <div class="info-item">
                                    <span class="info-label">Name:</span>
                                    <span class="info-value">{{ student_data.fullname }}</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-label">Student ID:</span>
                                    <span class="info-value">{{ student_data.studid }}</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-label">Gender:</span>
                                    <span class="info-value">{{ gender_display }}</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-label">Age:</span>
                                    <span class="info-value">{{ student_data.age }}</span>
                                </div>
                            </div>
                        </div>

                        <table class="grades-table">
                            <thead>
                                <tr>
                                    <th rowspan="2">Sem.</th>
                                    <th colspan="{{ subjects|length }}">Subjects</th>
                                    <th rowspan="2">Total</th>
                                    <th rowspan="2">Average</th>
                                    <th rowspan="2">Rank</th>
                                    <th rowspan="2">Conduct</th>
                                    <th rowspan="2">Remark</th>
                                </tr>
                                <tr>
                                    {% for subject in subjects %}
                                        <th>{{ subject_labels[subject] }}</th>
                                    {% endfor %}
                                </tr>
                            </thead>
                            <tbody>
                                <!-- First Semester Row -->
                                <tr class="semester-1st">
                                    <td>1st</td>
                                    {% for subject in subjects %}
                                        {% set score = scores['1'].get(subject) if scores['1'] else None %}
                                        {% if score is not none and score != 0 %}
                                            <td class="{% if score < 50 %}low-score{% endif %}">
                                                {{ score|int if score == score|int else score }}
                                            </td>
                                        {% else %}
                                            <td class="null-value">NULL</td>
                                        {% endif %}
                                    {% endfor %}
                                    <td class="summary-cell">
                                        {% if semester_totals['1'] is not none %}
                                            {{ semester_totals['1']|int if semester_totals['1'] == semester_totals['1']|int else semester_totals['1'] }}
                                        {% else %}
                                            NULL
                                        {% endif %}
                                    </td>
                                    <td class="summary-cell">
                                        {% if semester_averages['1'] is not none %}
                                            {{ "%.1f"|format(semester_averages['1']) }}
                                        {% else %}
                                            NULL
                                        {% endif %}
                                    </td>
                                    <td class="summary-cell rank-cell">{{ student_ranks.f_avg_rank }}</td>
                                    <td class="{{ 'conduct-poor' if conduct == 'Poor' else '' }}">{{ conduct }}</td>
                                    <td rowspan="3" class="{{ 'pass' if remark == 'Passed' else ('fail' if remark == 'Failed' else '') }}">
                                        {{ remark }}
                                    </td>
                                </tr>
                                
                                <!-- Second Semester Row -->
                                <tr class="semester-2nd">
                                    <td>2nd</td>
                                    {% for subject in subjects %}
                                        {% set score = scores['2'].get(subject) if scores['2'] else None %}
                                        {% if score is not none and score != 0 %}
                                            <td class="{% if score < 50 %}low-score{% endif %}">
                                                {{ score|int if score == score|int else score }}
                                            </td>
                                        {% else %}
                                            <td class="null-value">NULL</td>
                                        {% endif %}
                                    {% endfor %}
                                    <td class="summary-cell">
                                        {% if semester_totals['2'] is not none %}
                                            {{ semester_totals['2']|int if semester_totals['2'] == semester_totals['2']|int else semester_totals['2'] }}
                                        {% else %}
                                            NULL
                                        {% endif %}
                                    </td>
                                    <td class="summary-cell">
                                        {% if semester_averages['2'] is not none %}
                                            {{ "%.1f"|format(semester_averages['2']) }}
                                        {% else %}
                                            NULL
                                        {% endif %}
                                    </td>
                                    <td class="summary-cell rank-cell">{{ student_ranks.s_avg_rank }}</td>
                                    <td class="{{ 'conduct-poor' if conduct == 'Poor' else '' }}">{{ conduct }}</td>
                                </tr>
                                
                                <!-- Average Row -->
                                <tr class="semester-avr">
                                    <td>Avg.</td>
                                    {% for subject in subjects %}
                                        {% set avg = annual_averages.get(subject) %}
                                        {% if avg is not none %}
                                            <td class="{% if avg < 50 %}low-score{% endif %}">
                                                {{ "%.1f"|format(avg) }}
                                            </td>
                                        {% else %}
                                            <td class="null-value">NULL</td>
                                        {% endif %}
                                    {% endfor %}
                                    <td class="summary-cell">
                                        {% if annual_total_display is not none %}
                                            {{ "%.1f"|format(annual_total_display) }}
                                        {% else %}
                                            NULL
                                        {% endif %}
                                    </td>
                                    <td class="summary-cell">
                                        {% if overall_annual_avg is not none %}
                                            {{ "%.1f"|format(overall_annual_avg) }}
                                        {% else %}
                                            NULL
                                        {% endif %}
                                    </td>
                                    <td class="summary-cell rank-cell">{{ student_ranks.a_avg_rank }}</td>
                                    <td class="{{ 'conduct-poor' if conduct == 'Poor' else '' }}">{{ conduct }}</td>
                                </tr>
                            </tbody>
                        </table>

                        <div class="school-remark">
                            <div>School's Remark</div>
                            <div class="remark-line"></div>
                            <div class="remark-line"></div>
                            <div class="remark-line"></div>
                        </div>

                        <div class="footer">
                            <div class="signature-area">
                                <div class="teacher-signature">
                                    <div class="signature-line"></div>
                                    <div>Name of Home Room Teacher</div>
                                </div>
                                <div class="parent-signature">
                                    <div class="signature-line"></div>
                                    <div>Name & Sign of Parent or Guardian</div>
                                </div>
                                <div class="clear"></div>
                            </div>
                        </div>
                        
                        <div class="action-buttons">
                            <button class="print-btn" onclick="window.print()">Print Report Card</button>
                        </div>
                        
                    {% else %}
                        <div class="no-data">
                            {% if student_id %}
                                <p>No student data available for the selected student.</p>
                            {% else %}
                                <p>Please search for a student or select from the dropdown to generate a report card.</p>
                            {% endif %}
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="{{ url_for('static', filename='js/report_card.js') }}"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''',
    all_students=all_students,
    student_id=student_id,
    search_term=search_term,
    student_data=student_data,
    academic_info=academic_info,
    ethiopian_year=ethiopian_year,
    student_ranks=student_ranks,
    scores=scores,
    subjects=subjects,
    subject_labels=subject_labels,
    semester_totals=semester_totals,
    semester_averages=semester_averages,
    annual_averages=annual_averages,
    annual_total_display=annual_totals if annual_totals > 0 else None,
    overall_annual_avg=overall_annual_avg,
    remark=remark
    )