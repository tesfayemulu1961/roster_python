# subject_based_summary_analysis
from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
from datetime import datetime

director_subject_based_summary_analysis = Blueprint('director_subject_based_summary_analysis', __name__, url_prefix='/director')

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
    """Fetch dropdown options from database"""
    options = {}
    sql = f"SELECT {id_col}, {name_col} FROM {table}"
    if where:
        sql += f" WHERE {where}"
    cursor.execute(sql)
    for row in cursor.fetchall():
        options[row[id_col]] = row[name_col]
    return options

def get_ethiopian_year(greg_date):
    """Convert Gregorian date to Ethiopian year"""
    try:
        if isinstance(greg_date, str):
            timestamp = datetime.strptime(greg_date, '%Y-%m-%d')
        else:
            timestamp = greg_date
            
        gy = timestamp.year
        gm = timestamp.month
        gd = timestamp.day
        
        if gm < 9 or (gm == 9 and gd < 11):
            return gy - 8
        else:
            return gy - 7
    except:
        return "Unknown"

def calculate_average_scores(student_data, is_blind, grade_id):
    """Calculate average scores from both semesters"""
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
    averaged_scores = {}
    
    for subject in subjects:
        sem1 = student_data.get('sem1', {}).get(subject) if student_data.get('sem1') else None
        sem2 = student_data.get('sem2', {}).get(subject) if student_data.get('sem2') else None
        
        # Convert 0 to None
        if sem1 == 0:
            sem1 = None
        if sem2 == 0:
            sem2 = None
        
        # Calculate average if both semesters have scores
        if sem1 is not None and sem2 is not None:
            average = round((sem1 + sem2) / 2, 2)
        elif sem1 is not None:
            average = sem1
        elif sem2 is not None:
            average = sem2
        else:
            average = None
        
        averaged_scores[subject] = average
        
        if average is None:
            null_found = True
        else:
            total += average
            valid_scores += 1
    
    if null_found or valid_scores == 0:
        return {
            'total': None,
            'average': None,
            'rank': None,
            'subjects': subjects,
            'modified_scores': averaged_scores
        }
    else:
        average = total / len(subjects)
        return {
            'total': round(total, 2),
            'average': round(average, 2),
            'rank': None,
            'subjects': subjects,
            'modified_scores': averaged_scores
        }

@director_subject_based_summary_analysis.route('/get_sections_summary')
@login_required
def get_sections_summary():
    from flask import jsonify
    grade_id = request.args.get('grade_id', 0, type=int)
    sections = []
    if not grade_id:
        return jsonify(sections)
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT ID, sec_name FROM section WHERE grade_id = %s ORDER BY sec_name",
            (grade_id,)
        )
        sections = [{'id': row['ID'], 'name': row['sec_name']} for row in cursor.fetchall()]
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify(sections)


@director_subject_based_summary_analysis.route('/subject_based_summary_analysis')
@login_required
def subject_based_summary_analysis():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get filter values
    academic_year_id = request.args.get('year', 0, type=int)
    grade_id = request.args.get('grade', 0, type=int)
    section_id = request.args.get('section', 0, type=int)
    
    # Initialize variables
    students = []
    analysis = []
    show_analysis = False
    ethiopian_year = "Unknown"
    gender_totals = {'M': 0, 'F': 0}
    
    # Fetch dropdown options
    year_options = get_options(cursor, "academic_year", "ID", "year")
    grade_options = get_options(cursor, "grade", "ID", "level")
    
    section_options = {}
    if grade_id:
        section_options = get_options(cursor, "section", "ID", "sec_name", f"grade_id = {grade_id}")
    
    # Get Ethiopian year
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
    
    # Get room teacher if section selected
    room_teacher = {'name': 'Not Assigned', 'ID': 0}
    if section_id:
        room_teacher = get_room_teacher(cursor, section_id)
    
    # Only fetch students if all filters are selected
    if academic_year_id > 0 and grade_id > 0 and section_id > 0:
        # Get students in the specific section
        query = """
            SELECT s.RN, e.studid, s.fullname, s.gender, s.age, s.is_blind,
                   g.level AS grade, sec.sec_name AS section
            FROM student s
            JOIN enrollment e ON s.RN = e.student_RN 
                AND e.academic_year_id = s.academic_year_id
                AND e.grade_id = s.grade_id
                AND e.section_id = s.section_id
            JOIN grade g ON s.grade_id = g.ID
            JOIN section sec ON s.section_id = sec.ID
            WHERE s.grade_id = %s AND s.section_id = %s
            ORDER BY CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(e.studid, '/', -2), '/', 1) AS UNSIGNED) ASC
        """
        
        cursor.execute(query, (grade_id, section_id))
        student_records = {}
        
        for row in cursor.fetchall():
            student_records[row['RN']] = {
                'info': row,
                'sem1': {},
                'sem2': {}
            }
            
            # Count gender totals
            gender = row.get('gender')
            if gender in gender_totals:
                gender_totals[gender] += 1
        
        # If we have students, get their scores from both semesters
        if student_records:
            student_ids = list(student_records.keys())
            placeholders = ','.join(['%s'] * len(student_ids))
            
            # Get semester 1 scores
            query_sem1 = f"""
                SELECT student_RN, Amh, Eng, Maths, EnSc, Arts, HPE, Ethics,
                       GSc, SSc, Ctzp, IT, CTE
                FROM student_scores
                WHERE academic_year_id = %s AND grade_id = %s AND section_id = %s
                AND semester = '1'
                AND student_RN IN ({placeholders})
            """
            params = [academic_year_id, grade_id, section_id] + student_ids
            cursor.execute(query_sem1, tuple(params))
            
            for row in cursor.fetchall():
                if row['student_RN'] in student_records:
                    student_records[row['student_RN']]['sem1'] = row
            
            # Get semester 2 scores
            query_sem2 = f"""
                SELECT student_RN, Amh, Eng, Maths, EnSc, Arts, HPE, Ethics,
                       GSc, SSc, Ctzp, IT, CTE
                FROM student_scores
                WHERE academic_year_id = %s AND grade_id = %s AND section_id = %s
                AND semester = '2'
                AND student_RN IN ({placeholders})
            """
            cursor.execute(query_sem2, tuple(params))
            
            for row in cursor.fetchall():
                if row['student_RN'] in student_records:
                    student_records[row['student_RN']]['sem2'] = row
            
            # Process each student's scores
            for student_data in student_records.values():
                combined = {
                    **student_data['info'],
                    'sem1': student_data['sem1'],
                    'sem2': student_data['sem2']
                }
                is_blind = student_data['info']['is_blind'] == 1
                scores = calculate_average_scores(combined, is_blind, grade_id)
                students.append({**student_data['info'], **scores})
            
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
    
    # Perform analysis if showing results
    first_student_grade = ''
    first_student_section = ''
    
    if show_analysis:
        # Define subjects based on grade level
        if grade_id >= 11 and grade_id <= 12:
            subjects = ['Amh', 'Eng', 'Maths', 'GSc', 'SSc', 'Ctzp', 'IT', 'Arts', 'HPE', 'CTE']
        else:
            subjects = ['Amh', 'Eng', 'Maths', 'EnSc', 'Arts', 'HPE', 'Ethics']
        
        if students:
            first_student_grade = students[0].get('grade', '')
            first_student_section = students[0].get('section', '')
        
        # Analyze each subject
        for subject in subjects:
            subject_data = {
                'subject': subject,
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
                
                # Registered count (all students)
                subject_data['registered'][gender] += 1
                subject_data['registered']['T'] += 1
                
                # Check if student has this subject and has an average score
                if (subject in student.get('subjects', []) and 
                    subject in student.get('modified_scores', {}) and 
                    student['modified_scores'][subject] is not None):
                    
                    score = student['modified_scores'][subject]
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
                subject_data['lt50_pct'] = subject_data.get('lt50_pct', {})
                subject_data['gte50_pct'] = subject_data.get('gte50_pct', {})
                subject_data['gte75_pct'] = subject_data.get('gte75_pct', {})
                subject_data['gte85_pct'] = subject_data.get('gte85_pct', {})
                
                subject_data['lt50_pct'][gender] = round((subject_data['lt50'][gender] / examined * 100)) if examined > 0 else 0
                subject_data['gte50_pct'][gender] = round((subject_data['gte50'][gender] / examined * 100)) if examined > 0 else 0
                subject_data['gte75_pct'][gender] = round((subject_data['gte75'][gender] / examined * 100)) if examined > 0 else 0
                subject_data['gte85_pct'][gender] = round((subject_data['gte85'][gender] / examined * 100)) if examined > 0 else 0
            
            analysis.append(subject_data)
        
        # Calculate averages
        if analysis:
            averages = {
                'subject': 'Average',
                'registered': {'M': 0, 'F': 0, 'T': 0},
                'examined': {'M': 0, 'F': 0, 'T': 0},
                'lt50': {'M': 0, 'F': 0, 'T': 0},
                'lt50_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte50': {'M': 0, 'F': 0, 'T': 0},
                'gte50_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte75': {'M': 0, 'F': 0, 'T': 0},
                'gte75_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte85': {'M': 0, 'F': 0, 'T': 0},
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
                if subject_count > 0:
                    averages['registered'][gender] = round(averages['registered'][gender] / subject_count, 1)
                    averages['examined'][gender] = round(averages['examined'][gender] / subject_count, 1)
                    averages['lt50'][gender] = round(averages['lt50'][gender] / subject_count, 1)
                    averages['gte50'][gender] = round(averages['gte50'][gender] / subject_count, 1)
                    averages['gte75'][gender] = round(averages['gte75'][gender] / subject_count, 1)
                    averages['gte85'][gender] = round(averages['gte85'][gender] / subject_count, 1)
                
                # Calculate average percentages
                examined = averages['examined'][gender]
                averages['lt50_pct'][gender] = round((averages['lt50'][gender] / examined * 100)) if examined > 0 else 0
                averages['gte50_pct'][gender] = round((averages['gte50'][gender] / examined * 100)) if examined > 0 else 0
                averages['gte75_pct'][gender] = round((averages['gte75'][gender] / examined * 100)) if examined > 0 else 0
                averages['gte85_pct'][gender] = round((averages['gte85'][gender] / examined * 100)) if examined > 0 else 0
            
            analysis.append(averages)
    
    cursor.close()
    conn.close()
    
    return render_template_string(SUBJECT_BASED_TEMPLATE, 
                                  year_options=year_options,
                                  grade_options=grade_options,
                                  section_options=section_options,
                                  academic_year_id=academic_year_id,
                                  grade_id=grade_id,
                                  section_id=section_id,
                                  show_analysis=show_analysis,
                                  ethiopian_year=ethiopian_year,
                                  students=students,
                                  gender_totals=gender_totals,
                                  analysis=analysis,
                                  room_teacher=room_teacher,
                                  first_student_grade=first_student_grade,
                                  first_student_section=first_student_section)

# Helper function for room teacher
def get_room_teacher(cursor, section_id):
    teacher = {'name': 'Not Assigned', 'ID': 0}
    
    cursor.execute("""
        SELECT t.ID, t.name 
        FROM section s
        INNER JOIN teacher t ON s.teacher_id = t.ID
        WHERE s.ID = %s
    """, (section_id,))
    result = cursor.fetchone()
    if result and result.get('ID'):
        teacher = result
    else:
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
    
    return teacher

# Template for subject_based_summary_analysis
SUBJECT_BASED_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subject Based Summary Analysis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8fafc;
            color: #334155;
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
        .btn {
            padding: 0.625rem 1.25rem;
            border: none;
            border-radius: 0.5rem;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
        }
        .btn-primary {
            background-color: #7c3aed;
            color: white;
        }
        .search-form {
            background: white;
            padding: 1.75rem;
            border-radius: 0.75rem;
            margin-bottom: 2rem;
            border: 1px solid #e2e8f0;
            max-width: 800px;
            margin: 0 auto;
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
        }
        .form-control {
            width: 100%;
            padding: 0.625rem 0.875rem;
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
        }
        .results-container {
            background: white;
            border-radius: 0.75rem;
            padding: 1.75rem;
            margin-bottom: 2rem;
            border: 1px solid #e2e8f0;
            overflow-x: auto;
        }
        .alert-warning {
            background-color: #fef3c7;
            color: #92400e;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        .performance-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85em;
            min-width: 1200px;
        }
        .performance-table th, .performance-table td {
            padding: 8px 10px;
            border: 1px solid #ddd;
            text-align: center;
        }
        .performance-table thead tr {
            background-color: #4a6fa5;
            color: white;
        }
        .performance-table tbody tr:nth-child(even) {
            background-color: #f3f3f3;
        }
        .performance-table tbody tr.average-row {
            font-weight: bold;
            background-color: #e6f3ff;
        }
        .subject-col {
            text-align: left !important;
            font-weight: bold;
        }
        .percentage-col {
            color: #1a73e8;
            font-weight: 500;
        }
        .performance-table thead .percentage-col {
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="page-header">
            <h1><i class="fas fa-chart-line"></i> Subject Based Summary Analysis</h1>
            <a href="/director/director_dashboard" class="btn btn-primary">
                <i class="fas fa-arrow-left"></i> Back to Dashboard
            </a>
        </div>
        
        <div class="search-form">
            <h3><i class="fas fa-filter"></i> Filter Options</h3>
            <form method="GET">
                <div class="form-row">
                    <div class="form-group">
                        <label>Academic Year</label>
                        <select name="year" id="yearSelect" class="form-control" required onchange="loadSections()">
                            <option value="">-- Select --</option>
                            {% for id, year in year_options.items() %}
                                <option value="{{ id }}" {% if academic_year_id == id %}selected{% endif %}>{{ year }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Grade</label>
                        <select name="grade" id="gradeSelect" class="form-control" required onchange="loadSections()">
                            <option value="">-- Select --</option>
                            {% for id, grade in grade_options.items() %}
                                <option value="{{ id }}" {% if grade_id == id %}selected{% endif %}>{{ grade }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Section</label>
                        <select name="section" id="sectionSelect" class="form-control" required>
                            <option value="">-- Select --</option>
                            {% for id, section in section_options.items() %}
                                <option value="{{ id }}" {% if section_id == id %}selected{% endif %}>{{ section }}</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-search"></i> Generate Report
                </button>
                <script>
                function loadSections() {
                    const gradeId = document.getElementById('gradeSelect').value;
                    const sectionSelect = document.getElementById('sectionSelect');
                    sectionSelect.innerHTML = '<option value="">-- Loading... --</option>';
                    if (!gradeId) {
                        sectionSelect.innerHTML = '<option value="">-- Select --</option>';
                        return;
                    }
                    fetch(`/director/get_sections_summary?grade_id=${gradeId}`)
                        .then(r => r.json())
                        .then(data => {
                            sectionSelect.innerHTML = '<option value="">-- Select --</option>';
                            if (data.error) {
                                sectionSelect.innerHTML = `<option value="">Error: ${data.error}</option>`;
                                return;
                            }
                            if (data.length === 0) {
                                sectionSelect.innerHTML = '<option value="">No sections found</option>';
                                return;
                            }
                            data.forEach(s => {
                                const opt = document.createElement('option');
                                opt.value = s.id;
                                opt.textContent = s.name;
                                sectionSelect.appendChild(opt);
                            });
                        })
                        .catch(err => {
                            sectionSelect.innerHTML = `<option value="">Network error: ${err.message}</option>`;
                        });
                }
                </script>
            </form>
        </div>
        
        {% if show_analysis %}
        <div class="results-container">
            <div class="header-info">
                <center>
                    <h3>Subject Based Performance Summary Analysis</h3>
                    <h4>Academic Year: <b>{{ ethiopian_year }}</b> | Grade: <b>{{ first_student_grade }}</b> | Section: <b>{{ first_student_section }}</b> | Teacher: <b>{{ room_teacher.name }}</b></h4>
                    <h4>Total Students: <b>{{ gender_totals.M + gender_totals.F }} (M: {{ gender_totals.M }}, F: {{ gender_totals.F }})</b></h4>
                </center>
            </div>
            
            <table class="performance-table">
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
                        <th>M</th><th>F</th><th>T</th>
                        <th class="percentage-col">M%</th>
                        <th class="percentage-col">F%</th>
                        <th class="percentage-col">T%</th>
                        <th>M</th><th>F</th><th>T</th>
                        <th class="percentage-col">M%</th>
                        <th class="percentage-col">F%</th>
                        <th class="percentage-col">T%</th>
                        <th>M</th><th>F</th><th>T</th>
                        <th class="percentage-col">M%</th>
                        <th class="percentage-col">F%</th>
                        <th class="percentage-col">T%</th>
                        <th>M</th><th>F</th><th>T</th>
                        <th class="percentage-col">M%</th>
                        <th class="percentage-col">F%</th>
                        <th class="percentage-col">T%</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in analysis %}
                    <tr {% if item.subject == 'Average' %}class="average-row"{% endif %}>
                        <td class="subject-col">{{ item.subject }}</td>
                        <td>{{ item.registered.M }}</td>
                        <td>{{ item.registered.F }}</td>
                        <td>{{ item.registered.T }}</td>
                        <td>{{ item.examined.M }}</td>
                        <td>{{ item.examined.F }}</td>
                        <td>{{ item.examined.T }}</td>
                        <td>{{ item.lt50.M }}</td>
                        <td>{{ item.lt50.F }}</td>
                        <td>{{ item.lt50.T }}</td>
                        <td class="percentage-col">{{ item.lt50_pct.M }}%</td>
                        <td class="percentage-col">{{ item.lt50_pct.F }}%</td>
                        <td class="percentage-col">{{ item.lt50_pct.T }}%</td>
                        <td>{{ item.gte50.M }}</td>
                        <td>{{ item.gte50.F }}</td>
                        <td>{{ item.gte50.T }}</td>
                        <td class="percentage-col">{{ item.gte50_pct.M }}%</td>
                        <td class="percentage-col">{{ item.gte50_pct.F }}%</td>
                        <td class="percentage-col">{{ item.gte50_pct.T }}%</td>
                        <td>{{ item.gte75.M }}</td>
                        <td>{{ item.gte75.F }}</td>
                        <td>{{ item.gte75.T }}</td>
                        <td class="percentage-col">{{ item.gte75_pct.M }}%</td>
                        <td class="percentage-col">{{ item.gte75_pct.F }}%</td>
                        <td class="percentage-col">{{ item.gte75_pct.T }}%</td>
                        <td>{{ item.gte85.M }}</td>
                        <td>{{ item.gte85.F }}</td>
                        <td>{{ item.gte85.T }}</td>
                        <td class="percentage-col">{{ item.gte85_pct.M }}%</td>
                        <td class="percentage-col">{{ item.gte85_pct.F }}%</td>
                        <td class="percentage-col">{{ item.gte85_pct.T }}%</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% elif academic_year_id and grade_id and section_id %}
        <div class="alert-warning">
            <h3>No Data Found</h3>
            <p>No student records match the selected filters. Please check that scores have been entered.</p>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''