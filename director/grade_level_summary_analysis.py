# grade_level_summary_analysis.py
from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector

grade_level_summary_bp = Blueprint('grade_level_summary', __name__, url_prefix='/director')

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

def get_grade_name(grade_id):
    """Get grade level name - maps database grade_id to display name"""
    grades = {
        5: '1st', 6: '2nd', 7: '3rd', 8: '4th',
        9: '5th', 10: '6th', 11: '7th', 12: '8th'
    }
    return grades.get(grade_id, str(grade_id))

@grade_level_summary_bp.route('/grade_level_summary_analysis')
@login_required
def grade_level_summary_analysis():
    conn = get_db()
    
    # Get filter values
    academic_year_id = request.args.get('year', 0, type=int)
    
    # Get academic year options
    cursor = conn.cursor(dictionary=True)
    year_options = {}
    years_query = "SELECT ID, year FROM academic_year ORDER BY year DESC"
    cursor.execute(years_query)
    for row in cursor.fetchall():
        year_options[row['ID']] = row['year']
    
    grade_analysis = []
    grand_totals = {
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
    
    if academic_year_id > 0:
        # Get all grades with students in correct order (1st to 8th)
        grades_query = """
            SELECT DISTINCT grade_id FROM student_scores 
            WHERE academic_year_id = %s 
            ORDER BY 
                CASE grade_id
                    WHEN 5 THEN 1
                    WHEN 6 THEN 2
                    WHEN 7 THEN 3
                    WHEN 8 THEN 4
                    WHEN 9 THEN 5
                    WHEN 10 THEN 6
                    WHEN 11 THEN 7
                    WHEN 12 THEN 8
                    ELSE 99
                END ASC
        """
        cursor.execute(grades_query, (academic_year_id,))
        grades_result = cursor.fetchall()
        
        sum_counter = 1
        
        for idx, grade_row in enumerate(grades_result, start=1):
            grade_id = grade_row['grade_id']
            grade_data = {
                'grade_name': str(idx),
                'sum_label': f'Sum{sum_counter}',
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
            sum_counter += 1
            
            # Get all students for this grade
            students_query = """
                SELECT s.gender, 
                    AVG((sc.Amh + sc.Eng + sc.Maths + 
                        IFNULL(sc.EnSc, 0) + IFNULL(sc.Arts, 0) + 
                        IFNULL(sc.HPE, 0) + IFNULL(sc.Ethics, 0) + 
                        IFNULL(sc.GSc, 0) + IFNULL(sc.SSc, 0) + 
                        IFNULL(sc.Ctzp, 0) + IFNULL(sc.IT, 0) + 
                        IFNULL(sc.CTE, 0)) / 
                        (CASE 
                            WHEN sc.grade_id BETWEEN 11 AND 12 THEN 10 
                            ELSE 7 
                        END)) as avg_score
                    FROM student s
                    JOIN student_scores sc ON s.RN = sc.student_RN
                    WHERE sc.grade_id = %s 
                    AND sc.academic_year_id = %s
                    GROUP BY s.RN, s.gender
            """
            cursor.execute(students_query, (grade_id, academic_year_id))
            students_result = cursor.fetchall()
            
            for student in students_result:
                gender = student['gender']
                avg_score = student['avg_score']
                
                # Skip students with missing or invalid gender
                if gender not in ('M', 'F'):
                    continue
                
                # Count registered students
                grade_data['registered'][gender] += 1
                grade_data['registered']['T'] += 1
                grand_totals['registered'][gender] += 1
                grand_totals['registered']['T'] += 1
                
                if avg_score is not None:
                    # Count examined students
                    grade_data['examined'][gender] += 1
                    grade_data['examined']['T'] += 1
                    grand_totals['examined'][gender] += 1
                    grand_totals['examined']['T'] += 1
                    
                    if avg_score < 50:
                        grade_data['lt50'][gender] += 1
                        grade_data['lt50']['T'] += 1
                        grand_totals['lt50'][gender] += 1
                        grand_totals['lt50']['T'] += 1
                    else:
                        grade_data['gte50'][gender] += 1
                        grade_data['gte50']['T'] += 1
                        grand_totals['gte50'][gender] += 1
                        grand_totals['gte50']['T'] += 1
                        
                        if avg_score >= 75:
                            grade_data['gte75'][gender] += 1
                            grade_data['gte75']['T'] += 1
                            grand_totals['gte75'][gender] += 1
                            grand_totals['gte75']['T'] += 1
                            
                            if avg_score >= 85:
                                grade_data['gte85'][gender] += 1
                                grade_data['gte85']['T'] += 1
                                grand_totals['gte85'][gender] += 1
                                grand_totals['gte85']['T'] += 1
            
            # Calculate grade-level percentages
            for gender in ['M', 'F', 'T']:
                examined = grade_data['examined'][gender]
                grade_data['lt50_pct'][gender] = round((grade_data['lt50'][gender] / examined * 100), 1) if examined > 0 else 0
                grade_data['gte50_pct'][gender] = round((grade_data['gte50'][gender] / examined * 100), 1) if examined > 0 else 0
                grade_data['gte75_pct'][gender] = round((grade_data['gte75'][gender] / examined * 100), 1) if examined > 0 else 0
                grade_data['gte85_pct'][gender] = round((grade_data['gte85'][gender] / examined * 100), 1) if examined > 0 else 0
            
            grade_analysis.append(grade_data)
        
        # Calculate grand total percentages
        for gender in ['M', 'F', 'T']:
            examined = grand_totals['examined'][gender]
            grand_totals['lt50_pct'][gender] = round((grand_totals['lt50'][gender] / examined * 100), 1) if examined > 0 else 0
            grand_totals['gte50_pct'][gender] = round((grand_totals['gte50'][gender] / examined * 100), 1) if examined > 0 else 0
            grand_totals['gte75_pct'][gender] = round((grand_totals['gte75'][gender] / examined * 100), 1) if examined > 0 else 0
            grand_totals['gte85_pct'][gender] = round((grand_totals['gte85'][gender] / examined * 100), 1) if examined > 0 else 0
    
    cursor.close()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, 
                                  year_options=year_options,
                                  academic_year_id=academic_year_id,
                                  grade_analysis=grade_analysis,
                                  grand_totals=grand_totals)

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grade Level Summary Analysis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .summary-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.9em;
        }
        
        .summary-table th, .summary-table td {
            padding: 8px 10px;
            border: 1px solid #ddd;
            text-align: center;
        }
        
        .summary-table th {
            background-color: #2c3e50;
            color: white;
            position: sticky;
            top: 0;
        }
        
        .summary-table tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        .summary-table tr:hover {
            background-color: #e9ecef;
        }
        
        .grade-header-row {
            background-color: #e9ecef;
            font-weight: bold;
        }
        
        .sum-row {
            background-color: #ffffff;
            font-weight: bold;
        }
        
        .grandsum-row {
            background-color: #ced4da;
            font-weight: bold;
        }
        
        .subject-col {
            text-align: left;
            font-weight: bold;
        }
        
        .table-container {
            overflow-x: auto;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1 class="mb-4">Grade Level Summary Analysis</h1>
        
        <div class="card mb-4">
            <div class="card-body">
                <form method="GET" class="row g-3">
                    <div class="col-md-6">
                        <label for="year" class="form-label">Academic Year</label>
                        <select name="year" id="year" class="form-select" required>
                            <option value="">Select Academic Year</option>
                            {% for id, year in year_options.items() %}
                                <option value="{{ id }}" {% if academic_year_id == id %}selected{% endif %}>
                                    {{ year }}
                                </option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-12">
                        <button type="submit" class="btn btn-primary">Generate Report</button>
                        <a href="/director/grade_level_summary_analysis" class="btn btn-secondary">Reset</a>
                    </div>
                </form>
            </div>
        </div>
        
        {% if academic_year_id > 0 %}
        <div class="table-container">
            <table class="summary-table">
                <thead>
                    <tr>
                        <th rowspan="2">Grade Level</th>
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
                        <th>M%</th><th>F%</th><th>T%</th>
                        <th>M</th><th>F</th><th>T</th>
                        <th>M%</th><th>F%</th><th>T%</th>
                        <th>M</th><th>F</th><th>T</th>
                        <th>M%</th><th>F%</th><th>T%</th>
                        <th>M</th><th>F</th><th>T</th>
                        <th>M%</th><th>F%</th><th>T%</th>
                    </tr>
                </thead>
                <tbody>
                    {% for grade in grade_analysis %}
                        <tr class="grade-header-row">
                            <td class="subject-col">Grade {{ grade.grade_name }}</td>
                            <td colspan="30"></td>
                        </tr>
                        
                        <tr class="sum-row">
                            <td class="subject-col">Grade {{ grade.grade_name }} Total</td>
                            <!-- Registered -->
                            <td>{{ grade.registered.M }}</td>
                            <td>{{ grade.registered.F }}</td>
                            <td>{{ grade.registered.T }}</td>
                            <!-- Examined -->
                            <td>{{ grade.examined.M }}</td>
                            <td>{{ grade.examined.F }}</td>
                            <td>{{ grade.examined.T }}</td>
                            <!-- Score < 50 -->
                            <td>{{ grade.lt50.M }}</td>
                            <td>{{ grade.lt50.F }}</td>
                            <td>{{ grade.lt50.T }}</td>
                            <td>{{ grade.lt50_pct.M }}</td>
                            <td>{{ grade.lt50_pct.F }}</td>
                            <td>{{ grade.lt50_pct.T }}</td>
                            <!-- Score ≥ 50 -->
                            <td>{{ grade.gte50.M }}</td>
                            <td>{{ grade.gte50.F }}</td>
                            <td>{{ grade.gte50.T }}</td>
                            <td>{{ grade.gte50_pct.M }}</td>
                            <td>{{ grade.gte50_pct.F }}</td>
                            <td>{{ grade.gte50_pct.T }}</td>
                            <!-- Score ≥ 75 -->
                            <td>{{ grade.gte75.M }}</td>
                            <td>{{ grade.gte75.F }}</td>
                            <td>{{ grade.gte75.T }}</td>
                            <td>{{ grade.gte75_pct.M }}</td>
                            <td>{{ grade.gte75_pct.F }}</td>
                            <td>{{ grade.gte75_pct.T }}</td>
                            <!-- Score ≥ 85 -->
                            <td>{{ grade.gte85.M }}</td>
                            <td>{{ grade.gte85.F }}</td>
                            <td>{{ grade.gte85.T }}</td>
                            <td>{{ grade.gte85_pct.M }}</td>
                            <td>{{ grade.gte85_pct.F }}</td>
                            <td>{{ grade.gte85_pct.T }}</td>
                        </tr>
                    {% endfor %}
                    
                    <!-- Grand Total -->
                    <tr class="grandsum-row">
                        <td class="subject-col">GrandSum</td>
                        <!-- Registered -->
                        <td>{{ grand_totals.registered.M }}</td>
                        <td>{{ grand_totals.registered.F }}</td>
                        <td>{{ grand_totals.registered.T }}</td>
                        <!-- Examined -->
                        <td>{{ grand_totals.examined.M }}</td>
                        <td>{{ grand_totals.examined.F }}</td>
                        <td>{{ grand_totals.examined.T }}</td>
                        <!-- Score < 50 -->
                        <td>{{ grand_totals.lt50.M }}</td>
                        <td>{{ grand_totals.lt50.F }}</td>
                        <td>{{ grand_totals.lt50.T }}</td>
                        <td>{{ grand_totals.lt50_pct.M }}</td>
                        <td>{{ grand_totals.lt50_pct.F }}</td>
                        <td>{{ grand_totals.lt50_pct.T }}</td>
                        <!-- Score ≥ 50 -->
                        <td>{{ grand_totals.gte50.M }}</td>
                        <td>{{ grand_totals.gte50.F }}</td>
                        <td>{{ grand_totals.gte50.T }}</td>
                        <td>{{ grand_totals.gte50_pct.M }}</td>
                        <td>{{ grand_totals.gte50_pct.F }}</td>
                        <td>{{ grand_totals.gte50_pct.T }}</td>
                        <!-- Score ≥ 75 -->
                        <td>{{ grand_totals.gte75.M }}</td>
                        <td>{{ grand_totals.gte75.F }}</td>
                        <td>{{ grand_totals.gte75.T }}</td>
                        <td>{{ grand_totals.gte75_pct.M }}</td>
                        <td>{{ grand_totals.gte75_pct.F }}</td>
                        <td>{{ grand_totals.gte75_pct.T }}</td>
                        <!-- Score ≥ 85 -->
                        <td>{{ grand_totals.gte85.M }}</td>
                        <td>{{ grand_totals.gte85.F }}</td>
                        <td>{{ grand_totals.gte85.T }}</td>
                        <td>{{ grand_totals.gte85_pct.M }}</td>
                        <td>{{ grand_totals.gte85_pct.F }}</td>
                        <td>{{ grand_totals.gte85_pct.T }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        {% endif %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''