# ==============================================
# annual_average_analysis.py - FIXED VERSION
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import math

director_annual_average_analysis = Blueprint('director_annual_average_analysis', __name__, url_prefix='/director')

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
    modified_scores = {}
    
    for subject in subjects:
        sem1_score = student_data.get('sem1', {}).get(subject) if student_data.get('sem1') else None
        sem2_score = student_data.get('sem2', {}).get(subject) if student_data.get('sem2') else None
        
        if sem1_score == 0:
            sem1_score = None
        if sem2_score == 0:
            sem2_score = None
        
        if sem1_score is not None and sem2_score is not None:
            average = round((sem1_score + sem2_score) / 2, 2)
        elif sem1_score is not None:
            average = sem1_score
        elif sem2_score is not None:
            average = sem2_score
        else:
            average = None
        
        modified_scores[subject] = average
        
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
            'modified_scores': modified_scores
        }
    else:
        avg = total / len(subjects)
        return {
            'total': round(total, 2),
            'average': round(avg, 2),
            'rank': None,
            'subjects': subjects,
            'modified_scores': modified_scores
        }

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
    
    if section_id == 67:
        teacher = {'name': 'Meseret Wodaj', 'ID': 0}
    
    return teacher

@director_annual_average_analysis.route('/get_sections')
@login_required
def get_sections():
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


@director_annual_average_analysis.route('/annual_average_analysis')
@login_required
def annual_average_analysis_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    academic_year_id = request.args.get('year', 0, type=int)
    grade_id = request.args.get('grade', 0, type=int)
    section_id = request.args.get('section', 0, type=int)
    
    year_options = get_options(cursor, "academic_year", "ID", "year")
    grade_options = get_options(cursor, "grade", "ID", "level")
    
    section_options = {}
    if grade_id:
        section_options = get_options(cursor, "section", "ID", "sec_name", f"grade_id = {grade_id}")
    
    room_teacher = {'name': 'Not Assigned', 'ID': 0}
    if section_id:
        room_teacher = get_room_teacher(cursor, section_id)
    
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
    
    students = []
    analysis = []
    show_analysis = False
    gender_totals = {'M': 0, 'F': 0}
    first_student_grade = ''
    first_student_section = ''
    
    if grade_id >= 11 and grade_id <= 12:
        subjects = ['Amh', 'Eng', 'Maths', 'GSc', 'SSc', 'Ctzp', 'IT', 'Arts', 'HPE', 'CTE']
    else:
        subjects = ['Amh', 'Eng', 'Maths', 'EnSc', 'Arts', 'HPE', 'Ethics']
    
    if academic_year_id and grade_id and section_id:
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
            
            gender = row.get('gender')
            if gender in gender_totals:
                gender_totals[gender] += 1
            
            if not first_student_grade:
                first_student_grade = row.get('grade', '')
                first_student_section = row.get('section', '')
        
        if student_records:
            student_ids = list(student_records.keys())
            placeholders = ','.join(['%s'] * len(student_ids))
            
            # Semester 1
            query = f"""
                SELECT student_RN, Amh, Eng, Maths, EnSc, Arts, HPE, Ethics,
                       GSc, SSc, Ctzp, IT, CTE
                FROM student_scores
                WHERE academic_year_id = %s AND grade_id = %s 
                AND section_id = %s AND semester = '1'
                AND student_RN IN ({placeholders})
            """
            params = [academic_year_id, grade_id, section_id] + student_ids
            cursor.execute(query, tuple(params))
            for row in cursor.fetchall():
                if row['student_RN'] in student_records:
                    student_records[row['student_RN']]['sem1'] = row
            
            # Semester 2
            cursor.execute(query.replace("semester = '1'", "semester = '2'"), tuple(params))
            for row in cursor.fetchall():
                if row['student_RN'] in student_records:
                    student_records[row['student_RN']]['sem2'] = row
            
            for student in student_records.values():
                combined = {
                    'info': student['info'],
                    'sem1': student['sem1'],
                    'sem2': student['sem2']
                }
                is_blind = student['info']['is_blind'] == 1
                scores = calculate_average_scores(combined, is_blind, grade_id)
                students.append({**student['info'], **scores})
            
            if students:
                rankable = [s for s in students if s.get('total') is not None]
                rankable.sort(key=lambda x: x.get('total', 0), reverse=True)
                rank = 1
                for student in rankable:
                    student['rank'] = rank
                    rank += 1
                for student in students:
                    student['rank'] = None
                    for ranked in rankable:
                        if student['RN'] == ranked['RN']:
                            student['rank'] = ranked['rank']
                            break
                show_analysis = True
    
    if show_analysis:
        for subject in subjects:
            sd = {
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
                
                sd['registered'][gender] += 1
                sd['registered']['T'] += 1
                
                modified = student.get('modified_scores', {})
                if subject in modified and modified[subject] is not None:
                    score = modified[subject]
                    sd['examined'][gender] += 1
                    sd['examined']['T'] += 1
                    
                    if score < 50:
                        sd['lt50'][gender] += 1
                        sd['lt50']['T'] += 1
                    else:
                        sd['gte50'][gender] += 1
                        sd['gte50']['T'] += 1
                        if score >= 75:
                            sd['gte75'][gender] += 1
                            sd['gte75']['T'] += 1
                            if score >= 85:
                                sd['gte85'][gender] += 1
                                sd['gte85']['T'] += 1
            
            for g in ['M', 'F', 'T']:
                ex = sd['examined'][g]
                sd['lt50_pct'] = sd.get('lt50_pct', {})
                sd['gte50_pct'] = sd.get('gte50_pct', {})
                sd['gte75_pct'] = sd.get('gte75_pct', {})
                sd['gte85_pct'] = sd.get('gte85_pct', {})
                sd['lt50_pct'][g] = round((sd['lt50'][g] / ex * 100)) if ex > 0 else 0
                sd['gte50_pct'][g] = round((sd['gte50'][g] / ex * 100)) if ex > 0 else 0
                sd['gte75_pct'][g] = round((sd['gte75'][g] / ex * 100)) if ex > 0 else 0
                sd['gte85_pct'][g] = round((sd['gte85'][g] / ex * 100)) if ex > 0 else 0
            
            analysis.append(sd)
        
        # Averages
        avg = {
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
            for g in ['M', 'F', 'T']:
                avg['registered'][g] += item['registered'][g]
                avg['examined'][g] += item['examined'][g]
                avg['lt50'][g] += item['lt50'][g]
                avg['gte50'][g] += item['gte50'][g]
                avg['gte75'][g] += item['gte75'][g]
                avg['gte85'][g] += item['gte85'][g]
        
        cnt = len(analysis)
        for g in ['M', 'F', 'T']:
            avg['registered'][g] = round(avg['registered'][g] / cnt, 1)
            avg['examined'][g] = round(avg['examined'][g] / cnt, 1)
            avg['lt50'][g] = round(avg['lt50'][g] / cnt, 1)
            avg['gte50'][g] = round(avg['gte50'][g] / cnt, 1)
            avg['gte75'][g] = round(avg['gte75'][g] / cnt, 1)
            avg['gte85'][g] = round(avg['gte85'][g] / cnt, 1)
            
            ex = avg['examined'][g]
            avg['lt50_pct'][g] = round((avg['lt50'][g] / ex * 100)) if ex > 0 else 0
            avg['gte50_pct'][g] = round((avg['gte50'][g] / ex * 100)) if ex > 0 else 0
            avg['gte75_pct'][g] = round((avg['gte75'][g] / ex * 100)) if ex > 0 else 0
            avg['gte85_pct'][g] = round((avg['gte85'][g] / ex * 100)) if ex > 0 else 0
        
        analysis.append(avg)
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Annual Average Analysis</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f8fafc; color: #334155; }
            .container { max-width: 1400px; margin: 0 auto; }
            .search-form { background: white; padding: 1.75rem; border-radius: 0.75rem; margin-bottom: 2rem; border: 1px solid #e2e8f0; max-width: 800px; margin: 0 auto; }
            .form-row { display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.25rem; }
            .form-group { flex: 1; min-width: 180px; }
            .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
            .form-control { width: 100%; padding: 0.625rem 0.875rem; border: 1px solid #e2e8f0; border-radius: 0.5rem; }
            .btn { padding: 0.625rem 1.25rem; border: none; border-radius: 0.5rem; cursor: pointer; display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none; }
            .btn-primary { background-color: #7c3aed; color: white; }
            .btn-danger { background-color: #dc3545; color: white; }
            .form-actions { display: flex; gap: 0.75rem; margin-top: 1rem; }
            .teacher-selection { background-color: #e9f7ef; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: center; }
            .results-container { background: white; border-radius: 0.75rem; padding: 1.75rem; margin-bottom: 2rem; border: 1px solid #e2e8f0; overflow-x: auto; }
            .header-info { text-align: center; margin-bottom: 20px; }
            .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid #e2e8f0; }
            .page-header h1 { font-size: 1.8rem; font-weight: 600; margin: 0; display: flex; align-items: center; gap: 0.75rem; color: #1e293b; }
            .analysis-table { width: 100%; border-collapse: collapse; font-size: 0.85em; min-width: 1200px; }
            .analysis-table th, .analysis-table td { padding: 8px 10px; border: 1px solid #ddd; text-align: center; }
            .analysis-table thead tr { background-color: #4a6fa5; color: white; }
            .analysis-table tbody tr:nth-child(even) { background-color: #f3f3f3; }
            .analysis-table tbody tr.average-row { font-weight: bold; background-color: #e6f3ff; }
            .export-buttons { margin-bottom: 20px; display: flex; gap: 10px; justify-content: flex-end; }
            .alert-warning { background-color: #fef3c7; color: #92400e; padding: 15px; border-radius: 6px; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="page-header">
                <h1><i class="fas fa-chart-bar"></i> Annual Average Analysis</h1>
                <a href="/director/view_student_scores" class="btn btn-primary"><i class="fas fa-arrow-left"></i> Back to Scores</a>
            </div>

            {% if not (year_id and grade_id and section_id) %}
            <div class="search-form">
                <h2><i class="fas fa-filter"></i> Filter Students</h2>
                <form method="GET">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Academic Year</label>
                            <select name="year" id="yearSelect" class="form-control" required onchange="loadSections()">
                                <option value="">-- Select --</option>
                                {% for id, year in year_options.items() %}
                                    <option value="{{ id }}" {% if year_id == id %}selected{% endif %}>{{ year }}</option>
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
                        <script>
                        function loadSections() {
                            const gradeId = document.getElementById('gradeSelect').value;
                            const yearId = document.getElementById('yearSelect').value;
                            const sectionSelect = document.getElementById('sectionSelect');
                            sectionSelect.innerHTML = '<option value="">-- Loading... --</option>';
                            if (!gradeId) {
                                sectionSelect.innerHTML = '<option value="">-- Select --</option>';
                                return;
                            }
                            fetch(`/director/get_sections?grade_id=${gradeId}&year_id=${yearId}`)
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
                    </div>
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary"><i class="fas fa-search"></i> Search</button>
                        <a href="/director/annual_average_analysis" class="btn btn-danger"><i class="fas fa-times"></i> Clear</a>
                    </div>
                </form>
            </div>
            {% endif %}

            {% if show_analysis %}
            <div class="results-container">
                <div class="header-info">
                    <h3>Student Performance Analysis Report (Subject-based Annual Average Analysis)</h3>
                    <h4>Academic Year: <b>{{ ethiopian_year }}</b> | Grade: <b>{{ first_student_grade }}</b> | Section: <b>{{ first_student_section }}</b> | Teacher: <b>{{ room_teacher.name }}</b> | Total Students: <b>{{ gender_totals.M + gender_totals.F }} (M:{{ gender_totals.M }}, F:{{ gender_totals.F }})</b></h4>
                </div>
                
                <div class="export-buttons">
                    <button class="btn btn-primary" onclick="copyTable()"><i class="fas fa-copy"></i> Copy</button>
                    <button class="btn btn-primary" onclick="exportCSV()"><i class="fas fa-file-csv"></i> CSV</button>
                    <button class="btn btn-primary" onclick="exportExcel()"><i class="fas fa-file-excel"></i> Excel</button>
                    <button class="btn btn-primary" onclick="window.print()"><i class="fas fa-print"></i> Print</button>
                </div>
                
                <table class="analysis-table" id="dataTable">
                    <thead>
                        <tr><th rowspan="2">Subject</th><th colspan="3">Registered</th><th colspan="3">Examined</th><th colspan="6">Score &lt; 50</th><th colspan="6">Score ≥ 50</th><th colspan="6">Score ≥ 75</th><th colspan="6">Score ≥ 85</th></tr>
                        <tr><th>M</th><th>F</th><th>T</th><th>M</th><th>F</th><th>T</th><th>M</th><th>F</th><th>T</th><th>M%</th><th>F%</th><th>T%</th><th>M</th><th>F</th><th>T</th><th>M%</th><th>F%</th><th>T%</th><th>M</th><th>F</th><th>T</th><th>M%</th><th>F%</th><th>T%</th><th>M</th><th>F</th><th>T</th><th>M%</th><th>F%</th><th>T%</th></tr>
                    </thead>
                    <tbody>
                        {% for item in analysis %}
                        <tr {% if item.subject == 'Average' %}class="average-row"{% endif %}>
                            <td>{{ item.subject }}</td>
                            <td>{{ item.registered.M }}</td><td>{{ item.registered.F }}</td><td>{{ item.registered.T }}</td>
                            <td>{{ item.examined.M }}</td><td>{{ item.examined.F }}</td><td>{{ item.examined.T }}</td>
                            <td>{{ item.lt50.M }}</td><td>{{ item.lt50.F }}</td><td>{{ item.lt50.T }}</td>
                            <td>{{ item.lt50_pct.M }}%</td><td>{{ item.lt50_pct.F }}%</td><td>{{ item.lt50_pct.T }}%</td>
                            <td>{{ item.gte50.M }}</td><td>{{ item.gte50.F }}</td><td>{{ item.gte50.T }}</td>
                            <td>{{ item.gte50_pct.M }}%</td><td>{{ item.gte50_pct.F }}%</td><td>{{ item.gte50_pct.T }}%</td>
                            <td>{{ item.gte75.M }}</td><td>{{ item.gte75.F }}</td><td>{{ item.gte75.T }}</td>
                            <td>{{ item.gte75_pct.M }}%</td><td>{{ item.gte75_pct.F }}%</td><td>{{ item.gte75_pct.T }}%</td>
                            <td>{{ item.gte85.M }}</td><td>{{ item.gte85.F }}</td><td>{{ item.gte85.T }}</td>
                            <td>{{ item.gte85_pct.M }}%</td><td>{{ item.gte85_pct.F }}%</td><td>{{ item.gte85_pct.T }}%</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <script>
                function copyTable() {
                    const range = document.createRange();
                    range.selectNode(document.getElementById('dataTable'));
                    window.getSelection().removeAllRanges();
                    window.getSelection().addRange(range);
                    document.execCommand('copy');
                    window.getSelection().removeAllRanges();
                    alert('Table copied!');
                }
                function exportCSV() {
                    let csv = []; const rows = document.querySelectorAll('#dataTable tr');
                    for (let row of rows) {
                        let rowData = [];
                        for (let cell of row.cells) rowData.push('"' + cell.innerText.replace(/"/g, '""') + '"');
                        csv.push(rowData.join(','));
                    }
                    const blob = new Blob([csv.join('\\n')], {type: 'text/csv'});
                    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'annual_average.csv'; a.click(); URL.revokeObjectURL(a.href);
                }
                function exportExcel() {
                    let html = '<table border="1">';
                    for (let row of document.querySelectorAll('#dataTable tr')) {
                        html += '<tr>';
                        for (let cell of row.cells) html += '<td>' + cell.innerHTML + '<\/td>';
                        html += '<\/tr>';
                    }
                    html += '<\/table>';
                    const blob = new Blob([html], {type: 'application/vnd.ms-excel'});
                    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'annual_average.xls'; a.click(); URL.revokeObjectURL(a.href);
                }
            </script>
            {% elif year_id and grade_id and section_id %}
            <div class="alert-warning"><h3>No Data Found</h3><p>No student records match the selected filters. Please check that scores have been entered.</p></div>
            {% endif %}
            
            <div style="margin-top:20px;text-align:center"><a href="/director/director_dashboard" class="btn btn-primary"><i class="fas fa-arrow-left"></i> Back to Dashboard</a></div>
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
    analysis=analysis,
    show_analysis=show_analysis,
    room_teacher=room_teacher,
    ethiopian_year=ethiopian_year,
    gender_totals=gender_totals,
    first_student_grade=first_student_grade,
    first_student_section=first_student_section
    )