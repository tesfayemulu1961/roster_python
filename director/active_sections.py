# ==============================================
# Active Sections - Complete Python Conversion
# Converted from active_sections.php
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector

# Create blueprint
director_active_sections = Blueprint('director_active_sections', __name__, url_prefix='/director')

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

# Grade level to ID mapping (1st grade = 5, ..., 8th grade = 12)
GRADE_MAPPING = {
    1: 5, 2: 6, 3: 7, 4: 8,
    5: 9, 6: 10, 7: 11, 8: 12
}

# EC Year mapping for display
EC_YEAR_MAPPING = {
    1: {'ec_year': '2016', 'display': '2024-2025 (2016 EC)'},
    2: {'ec_year': '2017', 'display': '2025 (2017 EC)'},
    3: {'ec_year': '2018', 'display': '2025-2026 (2018 EC)'},
    4: {'ec_year': '2019', 'display': '2026-2027 (2019 EC)'}
}

@director_active_sections.route('/active_sections')
@login_required
def active_sections_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get selected academic year from URL, default to latest
    selected_ec_year = request.args.get('ec_year', '')
    
    # Fetch all available EC years from academic_year table
    cursor.execute("SELECT id, ec_year, year FROM academic_year ORDER BY ec_year DESC")
    academic_years = cursor.fetchall()
    
    available_ec_years = [year['ec_year'] for year in academic_years if year['ec_year']]
    
    # Also add any predefined years that might not be in the database yet
    for mapping in EC_YEAR_MAPPING.values():
        if mapping['ec_year'] not in available_ec_years:
            available_ec_years.append(mapping['ec_year'])
    
    available_ec_years.sort(reverse=True)
    
    # If no year selected and we have years, use the first one (latest)
    if not selected_ec_year and available_ec_years:
        selected_ec_year = available_ec_years[0]
    
    # Get the academic_year ID and details for the selected EC year
    selected_academic_year_id = None
    selected_academic_year_details = None
    selected_display = selected_ec_year
    
    if selected_ec_year:
        for year in academic_years:
            if year.get('ec_year') == selected_ec_year:
                selected_academic_year_details = year
                selected_academic_year_id = year['id']
                break
    
    # Get display name for selected EC year
    for mapping in EC_YEAR_MAPPING.values():
        if mapping['ec_year'] == selected_ec_year:
            selected_display = mapping['display']
            break
    
    # Initialize arrays for grade sections
    grade_sections = {}
    total_sections_with_students = 0
    total_students = 0
    
    # Get sections with students for each grade based on academic year
    for grade_level, grade_id in GRADE_MAPPING.items():
        if selected_academic_year_id:
            # Get sections with students for the selected academic year
            cursor.execute("""
                SELECT s.ID, s.sec_name, COUNT(DISTINCT e.studid) as student_count
                FROM section s
                INNER JOIN enrollment e ON s.ID = e.section_id
                WHERE s.grade_id = %s 
                    AND e.grade_id = %s 
                    AND e.academic_year_id = %s
                GROUP BY s.ID, s.sec_name
                HAVING student_count > 0
                ORDER BY s.sec_name
            """, (grade_id, grade_id, selected_academic_year_id))
        else:
            # Get sections with students from all years
            cursor.execute("""
                SELECT s.ID, s.sec_name, COUNT(DISTINCT e.studid) as student_count
                FROM section s
                INNER JOIN enrollment e ON s.ID = e.section_id
                WHERE s.grade_id = %s AND e.grade_id = %s
                GROUP BY s.ID, s.sec_name
                HAVING student_count > 0
                ORDER BY s.sec_name
            """, (grade_id, grade_id))
        
        sections = cursor.fetchall()
        
        # Calculate grade total students
        grade_student_count = sum(section['student_count'] for section in sections)
        total_students += grade_student_count
        
        grade_sections[grade_level] = {
            'grade_id': grade_id,
            'sections': sections,
            'section_count': len(sections),
            'student_count': grade_student_count
        }
        total_sections_with_students += len(sections)
    
    cursor.close()
    conn.close()
    
    # Prepare ec_year_mapping list for template
    ec_year_mapping_list = list(EC_YEAR_MAPPING.values())
    
    return render_template_string('''
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Active Sections With Students</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/core.css">
</head>
    <body>
        <div class="container py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2 class="mb-0"><i class="fas fa-door-open me-2"></i>Active Sections With Students</h2>
                <a href="/director/director_dashboard" class="btn btn-back"><i class="fas fa-arrow-left me-2"></i><b>Back to Dashboard</b></a>
            </div>
            
            <!-- Academic Year Filter -->
            <div class="card mb-4">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-3">
                            <label class="filter-label fw-bold">
                                <i class="fas fa-calendar-alt me-2"></i>Filter by Academic Year:
                            </label>
                        </div>
                        <div class="col-md-5">
                            <select id="academicYearSelect" class="form-select" onchange="window.location.href='?ec_year='+this.value">
                                <option value="">All Years</option>
                                {% for year in available_ec_years %}
                                    {% set display_year = year %}
                                    {% for mapping in ec_year_mapping %}
                                        {% if mapping.ec_year == year %}
                                            {% set display_year = mapping.display %}
                                        {% endif %}
                                    {% endfor %}
                                    <option value="{{ year }}" {% if selected_ec_year == year %}selected{% endif %}>
                                        {{ display_year }}
                                    </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-4 text-end">
                            {% if selected_ec_year %}
                                <div class="year-badge">
                                    <i class="fas fa-calendar-check me-1"></i>
                                    Selected: {{ selected_display }}
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Summary Card -->
            <div class="card summary-card mb-4">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4 text-center">
                            <h5>Total Active Sections</h5>
                            <p class="display-4 text-primary">{{ total_sections_with_students }}</p>
                        </div>
                        <div class="col-md-4 text-center">
                            <h5>Total Students</h5>
                            <p class="display-4 text-success">{{ total_students }}</p>
                        </div>
                        <div class="col-md-4 text-center">
                            <h5>Grade Range</h5>
                            <p class="mt-2">1st (ID 5) to 8th (ID 12)</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Grade Cards -->
            {% if total_sections_with_students > 0 %}
                <div class="row">
                    {% for grade_level in [1,2,3,4,5,6,7,8] %}
                        {% set grade_data = grade_sections[grade_level] %}
                        {% if grade_data.sections|length > 0 %}
                            <div class="col-md-6 col-lg-3 mb-4">
                                <div class="grade-card h-100">
                                    <div class="grade-header grade-{{ grade_level }}">
                                        <h4>
                                            <i class="fas fa-graduation-cap me-2"></i>Grade {{ grade_level }}
                                            <small class="float-end">ID: {{ grade_data.grade_id }}</small>
                                        </h4>
                                        <div class="d-flex justify-content-between mt-2">
                                            <span class="badge bg-light text-dark">
                                                <i class="fas fa-door-open me-1"></i>{{ grade_data.section_count }} Sections
                                            </span>
                                            <span class="badge bg-light text-dark">
                                                <i class="fas fa-user-graduate me-1"></i>{{ grade_data.student_count }} Students
                                            </span>
                                        </div>
                                    </div>
                                    <div class="card-body p-0">
                                        <table class="table table-sm table-hover mb-0">
                                            <thead>
                                                <tr>
                                                    <th>Section</th>
                                                    <th class="text-end">Students</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {% for section in grade_data.sections %}
                                                    <tr>
                                                        <td class="fw-bold">{{ section.sec_name }}</td>
                                                        <td class="text-end align-middle">
                                                            <span class="badge bg-primary rounded-pill">{{ section.student_count }}</span>
                                                        </td>
                                                    </tr>
                                                {% endfor %}
                                                <tr class="table-active">
                                                    <td><strong>Total</strong></td>
                                                    <td class="text-end"><strong>{{ grade_data.student_count }}</strong></td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        {% endif %}
                    {% endfor %}
                </div>
            {% else %}
                <div class="empty-state">
                    <i class="fas fa-door-open"></i>
                    <h4>No Active Sections</h4>
                    <p>There are currently no sections with enrolled students{% if selected_ec_year %} for the academic year {{ selected_display }}{% endif %}.</p>
                </div>
            {% endif %}
        </div>
        
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    available_ec_years=available_ec_years,
    selected_ec_year=selected_ec_year,
    selected_display=selected_display,
    ec_year_mapping=ec_year_mapping_list,
    total_sections_with_students=total_sections_with_students,
    total_students=total_students,
    grade_sections=grade_sections
    )