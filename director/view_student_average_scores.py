# ==============================================
# view_student_average_scores.py
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request, Response
from functools import wraps
import mysql.connector
import math
import csv
from io import StringIO

director_view_student_average_scores = Blueprint('director_view_student_average_scores', __name__, url_prefix='/director')

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

def get_all_student_scores(cursor, year_id, grade_id, section_id, search_term=""):
    """Get ALL students from enrollment table"""
    students = {}
    
    sql = """
        SELECT s.RN, e.studid, s.fullname, s.is_blind, s.gender, s.age
        FROM enrollment e
        INNER JOIN student s ON e.student_RN = s.RN
        WHERE e.academic_year_id = %s 
        AND e.grade_id = %s 
        AND e.section_id = %s
    """
    params = [year_id, grade_id, section_id]
    
    if search_term:
        sql += " AND (s.fullname LIKE %s OR e.studid LIKE %s)"
        search_param = f"%{search_term}%"
        params.extend([search_param, search_param])
    
    sql += " ORDER BY CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(e.studid, '/', -2), '/', 1) AS UNSIGNED) ASC"
    
    cursor.execute(sql, tuple(params))
    
    for row in cursor.fetchall():
        students[row['RN']] = {
            'id': row['RN'],
            'studid': row['studid'],
            'name': row['fullname'],
            'is_blind': row['is_blind'],
            'gender': row['gender'],
            'age': row['age'],
            'sem1': {},
            'sem2': {}
        }
    
    if not students:
        return students
    
    student_ids = list(students.keys())
    placeholders = ','.join(['%s'] * len(student_ids))
    
    # Semester 1 scores
    sql = f"""
        SELECT student_RN, Amh, Eng, Maths, EnSc, Arts, HPE, Ethics,
               GSc, SSc, Ctzp, IT, CTE
        FROM student_scores
        WHERE academic_year_id = %s AND grade_id = %s 
        AND section_id = %s AND semester = '1'
        AND student_RN IN ({placeholders})
    """
    params = [year_id, grade_id, section_id] + student_ids
    cursor.execute(sql, tuple(params))
    
    for row in cursor.fetchall():
        if row['student_RN'] in students:
            students[row['student_RN']]['sem1'] = row
    
    # Semester 2 scores
    sql = f"""
        SELECT student_RN, Amh, Eng, Maths, EnSc, Arts, HPE, Ethics,
               GSc, SSc, Ctzp, IT, CTE
        FROM student_scores
        WHERE academic_year_id = %s AND grade_id = %s 
        AND section_id = %s AND semester = '2'
        AND student_RN IN ({placeholders})
    """
    cursor.execute(sql, tuple(params))
    
    for row in cursor.fetchall():
        if row['student_RN'] in students:
            students[row['student_RN']]['sem2'] = row
    
    return students

def get_room_teacher(cursor, section_id, year_id):
    """Get room teacher for a section"""
    cursor.execute("""
        SELECT t.name 
        FROM teacher_assignment ta
        INNER JOIN teacher t ON ta.teacher_id = t.ID
        WHERE ta.section_id = %s AND ta.academic_year_id = %s AND ta.is_room_teacher = 1
        LIMIT 1
    """, (section_id, year_id))
    result = cursor.fetchone()
    if result:
        return result['name']
    return "Not Assigned"

def get_student_counts(cursor, year_id, grade_id, section_id):
    """Get male, female, and total student counts"""
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN gender = 'M' THEN 1 ELSE 0 END) as male_count,
            SUM(CASE WHEN gender = 'F' THEN 1 ELSE 0 END) as female_count
        FROM student 
        WHERE academic_year_id = %s AND grade_id = %s AND section_id = %s
    """, (year_id, grade_id, section_id))
    result = cursor.fetchone()
    male_count = result['male_count'] if result else 0
    female_count = result['female_count'] if result else 0
    return male_count, female_count, male_count + female_count

def get_failed_students_count(cursor, year_id, grade_id, section_id):
    """Count failed students (average < 50)"""
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

def process_student_data(students, grade_id):
    """Process student data and calculate averages"""
    processed = []
    subject_totals = {}
    subject_counts = {}
    
    # Determine all possible subjects
    if grade_id >= 11 and grade_id <= 12:
        all_subjects = ['Amh', 'Eng', 'Maths', 'GSc', 'SSc', 'Ctzp', 'IT', 'Arts', 'HPE', 'CTE']
    else:
        all_subjects = ['Amh', 'Eng', 'Maths', 'EnSc', 'Arts', 'HPE', 'Ethics']
    
    for student in students.values():
        is_blind = student['is_blind'] == 1
        
        # Determine subjects for blind students
        if is_blind:
            subjects = ['Amh', 'Eng', 'Arts', 'EnSc', 'HPE', 'Ethics'] if grade_id < 11 else ['Amh', 'Eng', 'Arts', 'HPE']
        else:
            subjects = all_subjects
        
        student_data = {
            'id': student['id'],
            'studid': student['studid'],
            'name': student['name'],
            'gender': student['gender'],
            'age': student['age'],
            'subjects': {},
            'sum': 0,
            'count': 0,
            'average': 0,
            'remark': 'Fail'
        }

        for subject in subjects:
            sem1_score = student['sem1'].get(subject) if student['sem1'] else None
            sem2_score = student['sem2'].get(subject) if student['sem2'] else None
            
            # Convert 0 to None
            if sem1_score == 0:
                sem1_score = None
            if sem2_score == 0:
                sem2_score = None
            
            subject_avg = None
            
            # Only calculate average if second semester score exists
            if sem2_score is not None:
                if sem1_score is not None:
                    subject_avg = (sem1_score + sem2_score) / 2
                else:
                    subject_avg = sem2_score
            
            student_data['subjects'][subject] = {
                'sem1': sem1_score,
                'sem2': sem2_score,
                'avg': subject_avg
            }
            
            if subject_avg is not None:
                student_data['sum'] += subject_avg
                student_data['count'] += 1
                
                if subject not in subject_totals:
                    subject_totals[subject] = 0
                    subject_counts[subject] = 0
                
                subject_totals[subject] += subject_avg
                subject_counts[subject] += 1
        
        if student_data['count'] > 0:
            student_data['average'] = student_data['sum'] / student_data['count']
            student_data['remark'] = 'Pass' if student_data['average'] >= 50 else 'Fail'
        
        processed.append(student_data)
    
    # Calculate subject averages
    subject_averages = {}
    for subject in subject_totals:
        subject_averages[subject] = subject_totals[subject] / subject_counts[subject]
    
    # Sort by average for ranking
    processed.sort(key=lambda x: x['average'], reverse=True)
    
    # Assign ranks
    rank = 1
    for i, student in enumerate(processed):
        if i > 0 and student['average'] == processed[i-1]['average']:
            student['rank'] = processed[i-1]['rank']
        else:
            student['rank'] = rank
        rank = student['rank'] + 1
    
    # Sort by studid for display
    processed.sort(key=lambda x: x['studid'])
    
    return {
        'students': processed,
        'subject_averages': subject_averages,
        'all_subjects': all_subjects
    }

@director_view_student_average_scores.route('/view_student_average_scores')
@login_required
def view_student_average_scores_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get filter values
    year_id = request.args.get('year', 0, type=int)
    grade_id = request.args.get('grade', 0, type=int)
    section_id = request.args.get('section', 0, type=int)
    search_term = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
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
    
    # Get names
    grade_name = ""
    section_name = ""
    academic_year_name = ""
    
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
    
    if year_id:
        cursor.execute("SELECT ec_year FROM academic_year WHERE ID = %s", (year_id,))
        result = cursor.fetchone()
        if result:
            academic_year_name = result['ec_year']
    
    # Initialize variables
    student_data = []
    subject_averages = {}
    processed_data = None
    male_count = 0
    female_count = 0
    total_students = 0
    failed_count = 0
    total_pages = 1
    current_page = page
    offset = (current_page - 1) * per_page
    room_teacher_name = "Not Assigned"
    
    if year_id and grade_id and section_id:
        # Get student counts
        male_count, female_count, total_students = get_student_counts(cursor, year_id, grade_id, section_id)
        
        # Get failed students count
        failed_count = get_failed_students_count(cursor, year_id, grade_id, section_id)
        
        # Get room teacher
        room_teacher_name = get_room_teacher(cursor, section_id, year_id)
        
        # Get all student scores
        all_students = get_all_student_scores(cursor, year_id, grade_id, section_id, search_term)
        
        # Process data and calculate ranks
        processed_data = process_student_data(all_students, grade_id)
        
        # Apply pagination
        total_students = len(processed_data['students'])
        total_pages = math.ceil(total_students / per_page) if total_students > 0 else 1
        start = offset
        end = offset + per_page
        student_data = processed_data['students'][start:end]
        subject_averages = processed_data['subject_averages']
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Student Average Report</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet">
        <link rel="stylesheet" href="{{ url_for('static', filename='css/student_average_scores.css') }}">
    </head>
    <body>
        <div class="container">
            <div class="page-header">
                <h1><i class="fas fa-chart-bar"></i> Semester Average Result Analysis</h1>
            </div>

            <div class="search-form">
                <h2><i class="fas fa-filter"></i> Filter Data</h2>
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
                            <select name="grade" class="form-control" required onchange="this.form.submit()">
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
                    
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-search"></i> Search
                        </button>
                        <a href="/director/view_student_average_scores" class="btn btn-secondary">
                            <i class="fas fa-times"></i> Clear
                        </a>
                    </div>
                </form>
            </div>

            {% if student_data %}
            <div class="header-info">
                <h3>Melkakole First and Medium School: Average Result Analysis</h3>
                <h4>
                    Academic Year: <b><u>{{ academic_year_name }}</u></b>&nbsp;&nbsp;&nbsp;
                    Grade: <b><u>{{ grade_name }}</u></b>&nbsp;&nbsp;&nbsp;
                    Section: <b><u>{{ section_name }}</u></b>&nbsp;&nbsp;&nbsp;
                    Teacher: <b><u>{{ room_teacher_name }}</u></b>
                </h4>
            </div>
            
            <!-- Statistics Section -->
            <div class="stats-container">
                <h3 class="stats-title"><i class="fas fa-users"></i> Student Statistics</h3>
                <div class="stats-grid">
                    <div class="stat-item bg-blue-50">
                        <div class="stat-name text-blue-600">Male Students</div>
                        <div class="stat-value text-blue-600">{{ male_count }}</div>
                    </div>
                    <div class="stat-item bg-pink-50">
                        <div class="stat-name text-pink-600">Female Students</div>
                        <div class="stat-value text-pink-600">{{ female_count }}</div>
                    </div>
                    <div class="stat-item bg-green-50">
                        <div class="stat-name text-green-600">Total Students</div>
                        <div class="stat-value text-green-600">{{ total_students }}</div>
                    </div>
                    <div class="stat-item bg-red-50">
                        <div class="stat-name text-red-600">Failed Students</div>
                        <div class="stat-value text-red-600">{{ failed_count }}</div>
                    </div>
                </div>
            </div>
            
            <!-- Subject Averages Section -->
            {% if subject_averages %}
            <div class="subject-avg-container">
                <h3 class="subject-avg-title"><i class="fas fa-book"></i> Subject Averages</h3>
                <div class="subject-avg-grid">
                    {% for subject, average in subject_averages.items() %}
                    <div class="subject-avg-item">
                        <div class="subject-name">{{ subject }}</div>
                        <div class="subject-avg">{{ "%.2f"|format(average) }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            
            <!-- Results Table -->
            <div class="results-container">
                <div class="search-section">
                    <h3 style="margin: 0;"><i class="fas fa-users"></i> Student Results</h3>
                    <form method="GET" style="margin: 0; display: flex; gap: 10px;">
                        <input type="hidden" name="year" value="{{ year_id }}">
                        <input type="hidden" name="grade" value="{{ grade_id }}">
                        <input type="hidden" name="section" value="{{ section_id }}">
                        <input type="text" name="search" class="form-control" placeholder="Search students..." 
                               value="{{ search_term }}" style="width: 250px;">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-search"></i> Search
                        </button>
                        {% if search_term %}
                        <a href="?year={{ year_id }}&grade={{ grade_id }}&section={{ section_id }}" class="btn btn-secondary">
                            <i class="fas fa-times"></i> Clear
                        </a>
                        {% endif %}
                    </form>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <a href="?year={{ year_id }}&grade={{ grade_id }}&section={{ section_id }}&export=csv" class="btn btn-primary">
                        <i class="fas fa-file-csv"></i> Export to CSV
                    </a>
                </div>
                
                <div class="table-responsive">
                    <table id="studentTable" class="table table-striped table-bordered" style="width:100%">
                        <thead>
                            <tr>
                                <th>No</th>
                                <th>ID</th>
                                <th>Full Name</th>
                                <th>Gender</th>
                                <th>Age</th>
                                {% for subject in processed_data.all_subjects %}
                                    <th>{{ subject }}</th>
                                {% endfor %}
                                <th class="total-column">Total</th>
                                <th class="average-column">Average</th>
                                <th class="rank-column">Rank</th>
                                <th>Remark</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for student in student_data %}
                            <tr>
                                <td>{{ loop.index + offset }}</td>
                                <td>{{ student.studid }}</td>
                                <td>{{ student.name }}</td>
                                <td>
                                    {% if student.gender == 'M' %}Male
                                    {% elif student.gender == 'F' %}Female
                                    {% else %}N/A{% endif %}
                                </td>
                                <td>{{ student.age if student.age else 'N/A' }}</td>
                                {% for subject in processed_data.all_subjects %}
                                    {% set avg = student.subjects[subject].avg if subject in student.subjects else None %}
                                    {% set cell_class = '' %}
                                    {% if avg is none %}
                                        {% set cell_class = 'null-value' %}
                                    {% elif avg < 50 %}
                                        {% set cell_class = 'low-score' %}
                                    {% endif %}
                                    <td class="{{ cell_class }}">
                                        {% if avg is not none %}
                                            {{ "%.2f"|format(avg) }}
                                        {% else %}
                                            <span class="null-value">NULL</span>
                                        {% endif %}
                                    </td>
                                {% endfor %}
                                <td class="total-column {% if student.sum == 0 %}null-value{% endif %}">
                                    {% if student.sum > 0 %}{{ "%.2f"|format(student.sum) }}{% else %}NULL{% endif %}
                                </td>
                                <td class="average-column {% if student.average == 0 %}null-value{% endif %}">
                                    {% if student.average > 0 %}{{ "%.2f"|format(student.average) }}{% else %}NULL{% endif %}
                                </td>
                                <td class="rank-column {% if student.rank is none %}null-value{% endif %}">
                                    {{ student.rank if student.rank else 'NULL' }}
                                </td>
                                <td class="{{ 'pass' if student.remark == 'Pass' else 'fail' }}">{{ student.remark }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                
                {% if total_pages > 1 %}
                <div class="pagination">
                    {% if current_page > 1 %}
                        <a href="?year={{ year_id }}&grade={{ grade_id }}&section={{ section_id }}&search={{ search_term }}&page={{ current_page - 1 }}">
                            &laquo; Previous
                        </a>
                    {% endif %}
                    
                    {% for p in range(1, total_pages + 1) %}
                        {% if p == current_page %}
                            <span class="current">{{ p }}</span>
                        {% else %}
                            <a href="?year={{ year_id }}&grade={{ grade_id }}&section={{ section_id }}&search={{ search_term }}&page={{ p }}">
                                {{ p }}
                            </a>
                        {% endif %}
                    {% endfor %}
                    
                    {% if current_page < total_pages %}
                        <a href="?year={{ year_id }}&grade={{ grade_id }}&section={{ section_id }}&search={{ search_term }}&page={{ current_page + 1 }}">
                            Next &raquo;
                        </a>
                    {% endif %}
                </div>
                {% endif %}
            </div>
            
            {% elif year_id and grade_id and section_id %}
            <div class="no-data">
                <h3>No Data Found</h3>
                <p>No student records match the selected filters.</p>
            </div>
            {% endif %}
            
            <div style="margin-top: 20px; text-align: center;">
                <a href="/director/director_dashboard" class="btn btn-primary">
                    <i class="fas fa-arrow-left"></i> Back to Dashboard
                </a>
            </div>
        </div>
        
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
        <script src="{{ url_for('static', filename='js/student_average_scores.js') }}"></script>
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
    search_term=search_term,
    current_page=current_page,
    total_pages=total_pages,
    student_data=student_data,
    processed_data=processed_data,
    subject_averages=subject_averages,
    grade_name=grade_name,
    section_name=section_name,
    academic_year_name=academic_year_name,
    room_teacher_name=room_teacher_name,
    male_count=male_count,
    female_count=female_count,
    total_students=total_students,
    failed_count=failed_count,
    offset=offset
    )

def export_to_csv(conn, year_id, grade_id, section_id, search_term):
    """Export student data to CSV"""
    cursor = conn.cursor(dictionary=True)
    
    # Get all students
    all_students = get_all_student_scores(cursor, year_id, grade_id, section_id, search_term)
    
    # Process data
    if grade_id >= 11 and grade_id <= 12:
        all_subjects = ['Amh', 'Eng', 'Maths', 'GSc', 'SSc', 'Ctzp', 'IT', 'Arts', 'HPE', 'CTE']
    else:
        all_subjects = ['Amh', 'Eng', 'Maths', 'EnSc', 'Arts', 'HPE', 'Ethics']
    
    processed = []
    for student in all_students.values():
        is_blind = student['is_blind'] == 1
        
        if is_blind:
            subjects = ['Amh', 'Eng', 'Arts', 'EnSc', 'HPE', 'Ethics'] if grade_id < 11 else ['Amh', 'Eng', 'Arts', 'HPE']
        else:
            subjects = all_subjects
        
        student_data = {
            'id': student['id'],
            'studid': student['studid'],
            'name': student['name'],
            'gender': student['gender'],
            'age': student['age'],
            'subjects': {},
            'sum': 0,
            'count': 0
        }
        
        for subject in subjects:
            sem1_score = student['sem1'].get(subject) if student['sem1'] else None
            sem2_score = student['sem2'].get(subject) if student['sem2'] else None
            
            if sem1_score == 0:
                sem1_score = None
            if sem2_score == 0:
                sem2_score = None
            
            subject_avg = None
            if sem2_score is not None:
                if sem1_score is not None:
                    subject_avg = (sem1_score + sem2_score) / 2
                else:
                    subject_avg = sem2_score
            
            student_data['subjects'][subject] = subject_avg
            
            if subject_avg is not None:
                student_data['sum'] += subject_avg
                student_data['count'] += 1
        
        if student_data['count'] > 0:
            student_data['average'] = student_data['sum'] / student_data['count']
        else:
            student_data['average'] = 0
        
        processed.append(student_data)
    
    # Calculate ranks
    processed.sort(key=lambda x: x['average'], reverse=True)
    rank = 1
    for i, student in enumerate(processed):
        if i > 0 and student['average'] == processed[i-1]['average']:
            student['rank'] = processed[i-1]['rank']
        else:
            student['rank'] = rank
        rank = student['rank'] + 1
    
    # Sort by studid for display
    processed.sort(key=lambda x: x['studid'])
    
    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    headers = ['No', 'ID', 'Full Name', 'Gender', 'Age'] + all_subjects + ['Total', 'Average', 'Rank', 'Remark']
    writer.writerow(headers)
    
    for i, student in enumerate(processed):
        remark = 'Pass' if student.get('average', 0) >= 50 else 'Fail'
        row = [i + 1, student['studid'], student['name'], student['gender'] or 'N/A', student['age'] or 'N/A']
        
        for subject in all_subjects:
            avg = student['subjects'].get(subject)
            row.append(round(avg, 2) if avg is not None else 'N/A')
        
        row.extend([round(student.get('sum', 0), 2), round(student.get('average', 0), 2), student.get('rank', ''), remark])
        writer.writerow(row)
    
    cursor.close()
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=student_average_report.csv'
    return response