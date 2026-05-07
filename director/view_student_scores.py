# ==============================================
# view_student_scores.py - With External CSS/JS
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import math

director_view_student_scores = Blueprint('director_view_student_scores', __name__, url_prefix='/director')

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

def calculate_scores(student_data, is_blind, grade_id):
    """Calculate total, average, and process scores for a student"""
    # Define subjects based on grade level
    if grade_id >= 11 and grade_id <= 12:
        all_subjects = ['Amh', 'Eng', 'Maths', 'GSc', 'SSc', 'Ctzp', 'IT', 'Arts', 'HPE', 'CTE']
    else:
        all_subjects = ['Amh', 'Eng', 'Maths', 'EnSc', 'Arts', 'HPE', 'Ethics']
    
    # For blind students
    if is_blind:
        if grade_id >= 11 and grade_id <= 12:
            subjects = ['Amh', 'Eng', 'Arts', 'HPE']
        else:
            subjects = ['Amh', 'Eng', 'Arts', 'EnSc', 'HPE', 'Ethics']
    else:
        subjects = all_subjects
    
    total = 0
    valid_scores = 0
    modified_scores = {}
    
    for subject in subjects:
        # Get score from student data
        score = student_data.get(subject)
        
        # Convert 0 to None
        if score == 0:
            score = None
        
        if score is not None:
            total += score
            valid_scores += 1
        
        modified_scores[subject] = score
    
    if valid_scores == 0:
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

def get_room_teacher(cursor, section_id, year_id):
    """Get room teacher for a section"""
    teacher = {'name': 'Not Assigned (System Error)', 'ID': 0}
    
    try:
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
                WHERE ta.section_id = %s 
                AND ta.academic_year_id = %s 
                AND ta.is_room_teacher = 1 
                LIMIT 1
            """, (section_id, year_id))
            result = cursor.fetchone()
            if result:
                teacher = result
    except Exception as e:
        print(f"Teacher lookup error: {e}")
        teacher = {'name': 'Not Assigned (Error)', 'ID': 0}
    
    # SPECIAL CASE: Force correct teacher for section 67
    if section_id == 67:
        teacher = {'name': 'Meseret Wodaj', 'ID': 0}
    
    return teacher

@director_view_student_scores.route('/view_student_scores')
@login_required
def view_student_scores_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get filter values
    year_id = request.args.get('year', 0, type=int)
    grade_id = request.args.get('grade', 0, type=int)
    section_id = request.args.get('section', 0, type=int)
    semester = request.args.get('semester', '1')
    
    # Fetch dropdown options
    cursor.execute("SELECT ID, year FROM academic_year ORDER BY year DESC")
    academic_years = cursor.fetchall()
    
    cursor.execute("SELECT ID, level FROM grade ORDER BY ID")
    grades = cursor.fetchall()
    
    # Get sections for selected grade
    section_options = []
    if grade_id:
        cursor.execute("SELECT ID, sec_name FROM section WHERE grade_id = %s ORDER BY sec_name", (grade_id,))
        section_options = cursor.fetchall()
    
    # Get room teacher
    room_teacher = {'name': 'Not Assigned (System Error)', 'ID': 0}
    if section_id and year_id:
        room_teacher = get_room_teacher(cursor, section_id, year_id)
    
    # Get Ethiopian year
    ethiopian_year = "Unknown"
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
    
    # Define all subjects for table headers
    if grade_id >= 11 and grade_id <= 12:
        all_subjects = ['Amh', 'Eng', 'Maths', 'GSc', 'SSc', 'Ctzp', 'IT', 'Arts', 'HPE', 'CTE']
    else:
        all_subjects = ['Amh', 'Eng', 'Maths', 'EnSc', 'Arts', 'HPE', 'Ethics']
    
    # Fetch and process student data
    students = []
    query_error = None
    
    if year_id > 0 and grade_id > 0 and section_id > 0:
        try:
            # Build subject columns based on grade level
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
                    AND e.academic_year_id = %s 
                    AND e.grade_id = %s 
                    AND e.section_id = %s
                JOIN student_scores ss ON s.RN = ss.student_RN 
                    AND ss.academic_year_id = %s 
                    AND ss.grade_id = %s 
                    AND ss.section_id = %s 
                    AND ss.semester = %s
                JOIN grade g ON ss.grade_id = g.ID
                JOIN section sec ON ss.section_id = sec.ID
                JOIN teacher t ON ss.teacher_id = t.ID
                JOIN academic_year ay ON ss.academic_year_id = ay.ID
                ORDER BY CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(e.studid, '/', -2), '/', 1) AS UNSIGNED) ASC
            """
            
            cursor.execute(query, (year_id, grade_id, section_id, year_id, grade_id, section_id, semester))
            results = cursor.fetchall()
            
            for row in results:
                is_blind = row['is_blind'] == 1
                scores = calculate_scores(row, is_blind, grade_id)
                
                student_data = dict(row)
                student_data.update(scores)
                students.append(student_data)
            
            # Calculate ranks based on average scores
            if students:
                # Separate students with and without valid averages
                students_with_avg = []
                students_without_avg = []
                
                for student in students:
                    if student['average'] is not None:
                        students_with_avg.append(student)
                    else:
                        students_without_avg.append(student)
                
                # Sort students with averages from highest to lowest
                students_with_avg.sort(key=lambda x: x['average'], reverse=True)
                
                # Assign ranks
                rank = 1
                for i, student in enumerate(students_with_avg):
                    if i > 0 and student['average'] == students_with_avg[i-1]['average']:
                        student['rank'] = students_with_avg[i-1]['rank']
                    else:
                        student['rank'] = rank
                    rank = student['rank'] + 1
                
                # Combine back and sort by studid for display
                students = students_with_avg + students_without_avg
                students.sort(key=lambda x: x['studid'])
                
        except Exception as e:
            query_error = str(e)
            print(f"Query error: {query_error}")
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Student Scores Management</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet">
        <link href="https://cdn.datatables.net/buttons/2.2.2/css/buttons.dataTables.min.css" rel="stylesheet">
        <link rel="stylesheet" href="{{ url_for('static', filename='css/student_scores.css') }}">
    </head>
    <body>
        <div class="container">
            <div class="page-header">
                <h1><i class="fas fa-users"></i> Student Scores Report</h1>
                <a href="/director/insert_student_scores" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Add Scores
                </a>
            </div>

            {% if not (year_id and grade_id and section_id) %}
            <div class="search-form">
                <h2><i class="fas fa-filter"></i> Filter Students</h2>
                <form method="GET">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Academic Year</label>
                            <select name="year" class="form-control" required>
                                <option value="">-- Select --</option>
                                {% for ay in academic_years %}
                                    <option value="{{ ay.ID }}" {% if year_id == ay.ID %}selected{% endif %}>{{ ay.year }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Grade</label>
                            <select name="grade" class="form-control" required>
                                <option value="">-- Select --</option>
                                {% for g in grades %}
                                    <option value="{{ g.ID }}" {% if grade_id == g.ID %}selected{% endif %}>{{ g.level }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Section</label>
                            <select name="section" class="form-control" required>
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
                        <a href="/director/view_student_scores" class="btn btn-danger">
                            <i class="fas fa-times"></i> Clear
                        </a>
                    </div>
                </form>
            </div>
            {% endif %}

            {% if query_error %}
            <div class="alert alert-danger">
                <h3>Database Error</h3>
                <p>{{ query_error }}</p>
            </div>
            {% endif %}

            {% if students %}
            <div class="results-container">
                <div class="header-info">
                    <h3>Melkakole First and Medium School: Student Scores</h3>
                    <h4>
                        <span>📅 Academic Year: <b><u>{{ ethiopian_year }}</u></b></span>
                        <span>📚 Grade: <b><u>{{ students[0].grade }}</u></b></span>
                        <span>🏫 Section: <b><u>{{ students[0].section }}</u></b></span>
                        <span>👨‍🏫 Teacher: <b><u>{{ room_teacher.name }}</u></b></span>
                        <span>📖 Semester: <b><u>{{ 'First' if semester == '1' else 'Second' }}</u></b></span>
                    </h4>
                </div>
                
                <table id="resultsTable" class="display nowrap" style="width:100%">
                    <thead>
                        <tr>
                            <th>No</th>
                            <th>Student ID</th>
                            <th>Full Name</th>
                            <th>Gender</th>
                            <th>Age</th>
                            {% for subject in all_subjects %}
                                <th>{{ subject }}</th>
                            {% endfor %}
                            <th class="total-column">Total</th>
                            <th class="average-column">Average</th>
                            <th class="rank-column">Rank</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for student in students %}
                        <tr {% if student.is_blind %}class="blind-row"{% endif %}>
                            <td>{{ loop.index }}</td>
                            <td>{{ student.studid }}</td>
                            <td>{{ student.fullname }}</td>
                            <td>{{ student.gender }}</td>
                            <td>{{ student.age }}</td>
                            
                            {% for subject in all_subjects %}
                                {% set score = student.modified_scores.get(subject) if subject in student.subjects else None %}
                                {% if score is not none %}
                                    <td class="{% if score < 50 %}low-score{% endif %}">
                                        {{ score|round(1) if score % 1 != 0 else score|int }}
                                    </td>
                                {% else %}
                                    <td class="null-value">NULL{% endif %}
                                </td>
                            {% endfor %}
                            
                            <td class="total-column">
                                {% if student.total is not none %}
                                    {{ student.total }}
                                {% else %}
                                    <span class="null-value">NULL</span>
                                {% endif %}
                            </td>
                            <td class="average-column">
                                {% if student.average is not none %}
                                    {{ student.average }}
                                {% else %}
                                    <span class="null-value">NULL</span>
                                {% endif %}
                            </td>
                            <td class="rank-column">
                                {% if student.rank is not none %}
                                    {{ student.rank }}
                                {% else %}
                                    <span class="null-value">NULL</span>
                                {% endif %}
                            </td>
                            <td>
                                <div class="action-buttons">
                                    <a href="/director/edit_student_scores?id={{ student.RN }}&semester={{ semester }}" 
                                       class="btn btn-primary btn-sm" title="Edit">
                                        <i class="fas fa-edit"></i>
                                    </a>
                                    <a href="/director/delete_student_scores?id={{ student.RN }}&semester={{ semester }}" 
                                       class="btn btn-danger btn-sm delete-btn" title="Delete">
                                        <i class="fas fa-trash-alt"></i>
                                    </a>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            {% elif year_id and grade_id and section_id %}
            <div class="alert alert-danger">
                <h3>No Results Found</h3>
                <p>No student records match the selected filters.</p>
                <p>Please check that:</p>
                <ul>
                    <li>Scores have been entered for this section</li>
                    <li>The selected room teacher is correct</li>
                    <li>The semester selection is correct</li>
                </ul>
            </div>
            {% endif %}

            <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: center;">
                <a href="/director/director_dashboard" class="btn btn-primary">
                    <i class="fas fa-arrow-left"></i> Back to Dashboard
                </a>
                <button onclick="window.location.reload()" class="btn btn-primary refresh-btn">
                    <i class="fas fa-sync-alt"></i> Refresh Page
                </button>
            </div>
        </div>

        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.2.2/js/dataTables.buttons.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.2.2/js/buttons.html5.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.2.2/js/buttons.print.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.1.3/jszip.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.53/pdfmake.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.53/vfs_fonts.js"></script>
        <script src="{{ url_for('static', filename='js/student_scores.js') }}"></script>
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
    students=students,
    all_subjects=all_subjects,
    room_teacher=room_teacher,
    ethiopian_year=ethiopian_year,
    query_error=query_error
    )