# ==============================================
# Student Statistics - Complete Python Version
# Converted from student_statistics.php
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
from collections import defaultdict

# Create blueprint
director_student_statistics = Blueprint('director_student_statistics', __name__, url_prefix='/director')

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

# Grade display names mapping
GRADE_DISPLAY_NAMES = {
    5: '1st', 6: '2nd', 7: '3rd', 8: '4th',
    9: '5th', 10: '6th', 11: '7th', 12: '8th'
}

# Template
STUDENT_STATISTICS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <link rel="stylesheet" href="/static/css/core.css">
    <meta charset="UTF-8">
    <title>Student Statistics</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
</head>
<body class="bg-light">
<div class="container py-4">
    <a href="/director/director_dashboard" class="btn btn-secondary back-link">
        <i class="fas fa-arrow-left"></i> Back to Dashboard
    </a>
    
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-users"></i> Student Statistics</h2>
        <form method="GET" class="d-flex align-items-center bg-white p-2 rounded shadow-sm border">
            <label class="me-2 small fw-bold text-nowrap">Filter Year:</label>
            <select name="academic_year_id" class="form-select form-select-sm" onchange="this.form.submit()">
                {% for year in academic_years %}
                    <option value="{{ year.id }}" {% if selected_year_id == year.id %}selected{% endif %}>{{ year.year }}</option>
                {% endfor %}
            </select>
        </form>
    </div>

    {% if selected_year_id != 3 %}
    <div class="row mb-4 text-center">
        <div class="col-md-4">
            <div class="card p-3 border-success">
                <strong>Passed: {{ total_passed_male + total_passed_female }}</strong>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-3 border-danger">
                <strong>Failed: {{ total_failed_male + total_failed_female }}</strong>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-3 border-warning">
                <strong>Incomplete: {{ total_incomplete_male + total_incomplete_female }}</strong>
            </div>
        </div>
    </div>
    {% endif %}

    <div class="row">
        {% for grade_data in grades_data %}
        <div class="col-lg-6 mb-4">
            <div class="grade-card bg-white">
                <div class="grade-header">
                    <h5 class="mb-0">{{ grade_data.grade_display }} Grade</h5>
                </div>
                <div class="table-responsive">
                    <table class="table table-sm table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Section</th>
                                <th class="text-center">Enrolled (M/F)</th>
                                {% if selected_year_id != 3 %}
                                <th class="text-center">Passed</th>
                                <th class="text-center">Failed</th>
                                <th class="text-center">Inc.</th>
                                {% endif %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for section in grade_data.sections %}
                            <tr>
                                <td class="fw-bold ps-3">{{ section.section_name }}</td>
                                <td class="text-center">
                                    <span class="male-count">{{ section.students_male }}</span> / 
                                    <span class="female-count">{{ section.students_female }}</span>
                                </td>
                                {% if selected_year_id != 3 %}
                                <td class="text-center"><span class="passed-count">{{ section.passed_male + section.passed_female }}</span></td>
                                <td class="text-center"><span class="failed-count">{{ section.failed_male + section.failed_female }}</span></td>
                                <td class="text-center"><span class="incomplete-count">{{ section.incomplete_male + section.incomplete_female }}</span></td>
                                {% endif %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
    <script src="/static/js/core.js"></script>
</body>
</html>
'''

@director_student_statistics.route('/student_statistics')
@login_required
def student_statistics_page():
    """Student Statistics - Complete conversion from PHP"""
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Fetch available Academic Years for the dropdown
    cursor.execute("SELECT id, year FROM academic_year ORDER BY year DESC")
    academic_years = cursor.fetchall()
    
    # Get the selected year (default to the most recent one)
    selected_year_id = request.args.get('academic_year_id', type=int)
    if not selected_year_id and academic_years:
        selected_year_id = academic_years[0]['id']
    
    # 2. Get grades 5-12 with sections filtered by Year
    cursor.execute("""
        SELECT g.ID as grade_id, g.level as grade_level, 
               s.ID as section_id, s.sec_name as section_name
        FROM grade g
        JOIN section s ON g.ID = s.grade_id
        WHERE g.ID BETWEEN 5 AND 12
        AND EXISTS (SELECT 1 FROM student st WHERE st.section_id = s.ID AND st.academic_year_id = %s)
        ORDER BY g.ID, s.sec_name
    """, (selected_year_id,))
    grade_sections = cursor.fetchall()
    
    # Initialize data structure
    grades_data = {}
    for row in grade_sections:
        grade_id = row['grade_id']
        if grade_id not in grades_data:
            grades_data[grade_id] = {
                'grade_level': row['grade_level'],
                'grade_display': GRADE_DISPLAY_NAMES.get(grade_id, str(grade_id)),
                'sections': []
            }
    
    # Create section data structure for each grade
    for grade_id in grades_data:
        grade_sections_dict = {}
        for row in grade_sections:
            if row['grade_id'] == grade_id:
                grade_sections_dict[row['section_id']] = {
                    'section_id': row['section_id'],
                    'section_name': row['section_name'],
                    'students_male': 0,
                    'students_female': 0,
                    'passed_male': 0,
                    'passed_female': 0,
                    'failed_male': 0,
                    'failed_female': 0,
                    'incomplete_male': 0,
                    'incomplete_female': 0
                }
        grades_data[grade_id]['sections'] = grade_sections_dict
    
    # 3. Get student data filtered by Year
    cursor.execute("""
        SELECT s.section_id, s.RN, UPPER(TRIM(s.gender)) as gender, s.is_blind,
               sc1.Amh as Amh_s1, sc1.Eng as Eng_s1, sc1.Maths as Maths_s1,
               sc1.Gsc as GSC_s1, sc1.SSc as SSC_s1, sc1.Ctzp as Ctzp_s1,
               sc1.Arts as Arts_s1, sc1.HPE as HPE_s1, sc1.CTE as CTE_s1, sc1.Ethics as Ethics_s1, sc1.EnSc as EnSc_s1,
               sc2.Amh as Amh_s2, sc2.Eng as Eng_s2, sc2.Maths as Maths_s2,
               sc2.Gsc as GSC_s2, sc2.SSc as SSC_s2, sc2.Ctzp as Ctzp_s2,
               sc2.Arts as Arts_s2, sc2.HPE as HPE_s2, sc2.CTE as CTE_s2, sc2.Ethics as Ethics_s2, sc2.EnSc as EnSc_s2
        FROM student s
        LEFT JOIN student_scores sc1 ON s.RN = sc1.student_RN AND sc1.semester = 1 AND sc1.academic_year_id = %s
        LEFT JOIN student_scores sc2 ON s.RN = sc2.student_RN AND sc2.semester = 2 AND sc2.academic_year_id = %s
        WHERE s.academic_year_id = %s 
        AND s.section_id IN (SELECT ID FROM section WHERE grade_id BETWEEN 5 AND 12)
    """, (selected_year_id, selected_year_id, selected_year_id))
    students = cursor.fetchall()
    
    # 4. Process each student
    for student in students:
        section_id = student['section_id']
        
        # Find which grade this section belongs to
        grade_id = None
        for gid, grade_data in grades_data.items():
            if section_id in grade_data['sections']:
                grade_id = gid
                break
        
        if not grade_id:
            continue
        
        section_data = grades_data[grade_id]['sections'][section_id]
        gender_key = 'male' if student['gender'] == 'M' else 'female'
        
        # Update student count
        if gender_key == 'male':
            section_data['students_male'] += 1
        else:
            section_data['students_female'] += 1
        
        # Skip Pass/Fail logic if academic_year_id is 3
        if selected_year_id == 3:
            continue
        
        # --- Pass/Fail Logic (only runs if year != 3) ---
        is_incomplete = False
        
        # Define required fields based on grade and blind status
        if 5 <= grade_id <= 10:  # Grades 1-6 (using EnSc)
            if student.get('is_blind') == 1:
                required_fields = ['Amh_s1', 'Amh_s2', 'Eng_s1', 'Eng_s2', 'Arts_s1', 'Arts_s2', 'HPE_s1', 'HPE_s2', 'Ethics_s1', 'Ethics_s2']
            else:
                required_fields = ['Amh_s1', 'Amh_s2', 'Eng_s1', 'Eng_s2', 'Maths_s1', 'Maths_s2', 'EnSc_s1', 'EnSc_s2', 'Arts_s1', 'Arts_s2', 'HPE_s1', 'HPE_s2', 'Ethics_s1', 'Ethics_s2']
        else:  # Grades 7-8 (using GSC, SSC, CTE)
            if student.get('is_blind') == 1:
                required_fields = ['Amh_s1', 'Amh_s2', 'Eng_s1', 'Eng_s2', 'SSC_s1', 'SSC_s2', 'Ctzp_s1', 'Ctzp_s2', 'Arts_s1', 'Arts_s2', 'HPE_s1', 'HPE_s2']
            else:
                required_fields = ['Amh_s1', 'Amh_s2', 'Eng_s1', 'Eng_s2', 'Maths_s1', 'Maths_s2', 'GSC_s1', 'GSC_s2', 'SSC_s1', 'SSC_s2', 'Ctzp_s1', 'Ctzp_s2', 'Arts_s1', 'Arts_s2', 'HPE_s1', 'HPE_s2', 'CTE_s1', 'CTE_s2']
        
        # Check for incomplete (null values)
        for field in required_fields:
            if student.get(field) is None:
                is_incomplete = True
                break
        
        if is_incomplete:
            if gender_key == 'male':
                section_data['incomplete_male'] += 1
            else:
                section_data['incomplete_female'] += 1
        else:
            # Calculate average score
            total_score = 0
            for field in required_fields:
                total_score += float(student.get(field, 0))
            
            final_average = total_score / len(required_fields)
            
            if final_average < 50:
                if gender_key == 'male':
                    section_data['failed_male'] += 1
                else:
                    section_data['failed_female'] += 1
            else:
                if gender_key == 'male':
                    section_data['passed_male'] += 1
                else:
                    section_data['passed_female'] += 1
    
    cursor.close()
    conn.close()
    
    # Convert sections from dict to list for template iteration
    for grade_id in grades_data:
        grades_data[grade_id]['sections'] = list(grades_data[grade_id]['sections'].values())
    
    # 5. Calculate global totals
    total_passed_male = 0
    total_passed_female = 0
    total_failed_male = 0
    total_failed_female = 0
    total_incomplete_male = 0
    total_incomplete_female = 0
    
    for grade_data in grades_data.values():
        for section in grade_data['sections']:
            total_passed_male += section['passed_male']
            total_passed_female += section['passed_female']
            total_failed_male += section['failed_male']
            total_failed_female += section['failed_female']
            total_incomplete_male += section['incomplete_male']
            total_incomplete_female += section['incomplete_female']
    
    # Convert grades_data to list for template
    grades_data_list = list(grades_data.values())
    
    return render_template_string(
        STUDENT_STATISTICS_TEMPLATE,
        academic_years=academic_years,
        selected_year_id=selected_year_id,
        grades_data=grades_data_list,
        total_passed_male=total_passed_male,
        total_passed_female=total_passed_female,
        total_failed_male=total_failed_male,
        total_failed_female=total_failed_female,
        total_incomplete_male=total_incomplete_male,
        total_incomplete_female=total_incomplete_female
    )