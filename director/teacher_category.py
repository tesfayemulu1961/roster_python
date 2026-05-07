# ==============================================
# Teacher Category - Complete Python Conversion
# Converted from teacher_category.php
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector

# Create blueprint
director_teacher_category = Blueprint('director_teacher_category', __name__, url_prefix='/director')

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

# Grade header colors
GRADE_COLORS = {
    1: 'grade-1', 2: 'grade-2', 3: 'grade-3', 4: 'grade-4',
    5: 'grade-5', 6: 'grade-6', 7: 'grade-7', 8: 'grade-8'
}

@director_teacher_category.route('/teacher_category')
@login_required
def teacher_category_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get selected academic year from URL, default to latest
    selected_ec_year = request.args.get('ec_year', '')
    
    # Fetch all available EC years from academic_year table
    cursor.execute("SELECT id, ec_year, year FROM academic_year ORDER BY ec_year DESC")
    academic_years = cursor.fetchall()
    
    available_ec_years = [year['ec_year'] for year in academic_years]
    
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
            if year['ec_year'] == selected_ec_year:
                selected_academic_year_details = year
                selected_academic_year_id = year['id']
                break
    
    # Get display name for selected EC year
    for mapping in EC_YEAR_MAPPING.values():
        if mapping['ec_year'] == selected_ec_year:
            selected_display = mapping['display']
            break
    
    # Get all active teachers for count display
    cursor.execute("SELECT ID, name FROM teacher WHERE status = 'active'")
    teachers = cursor.fetchall()
    
    # Initialize arrays for all possible grades (1-8)
    room_teachers = {grade: {} for grade in GRADE_MAPPING.keys()}
    subject_teachers = {grade: {} for grade in GRADE_MAPPING.keys()}
    grade_sections = {grade: [] for grade in GRADE_MAPPING.keys()}
    
    # Get teacher assignments from teacher_assignment table for the selected academic year
    if selected_academic_year_id:
        # Fetch room teacher assignments (is_room_teacher = 1 and section_id > 0)
        cursor.execute("""
            SELECT ta.teacher_id, ta.section_id, ta.academic_year_id, ta.grade_id,
                   t.name as teacher_name, s.sec_name
            FROM teacher_assignment ta
            INNER JOIN teacher t ON ta.teacher_id = t.ID
            INNER JOIN section s ON ta.section_id = s.ID
            WHERE ta.academic_year_id = %s 
                AND ta.is_room_teacher = 1
                AND ta.section_id > 0
                AND t.status = 'active'
        """, (selected_academic_year_id,))
        room_assignments = cursor.fetchall()
        
        # Organize room teachers by grade and section
        for assignment in room_assignments:
            # Find the grade level from grade_id
            grade_level = None
            for level, gid in GRADE_MAPPING.items():
                if gid == assignment['grade_id']:
                    grade_level = level
                    break
            
            if grade_level:
                section_name = assignment['sec_name'].strip()
                room_teachers[grade_level][section_name] = {
                    'teacher_name': assignment['teacher_name'],
                    'teacher_id': assignment['teacher_id'],
                    'section_id': assignment['section_id']
                }
        
        # Fetch subject teacher assignments (is_subject_teacher = 1 and subject_id > 0)
        cursor.execute("""
            SELECT ta.teacher_id, ta.section_id, ta.academic_year_id, ta.subject_id, ta.grade_id,
                   t.name as teacher_name, s.sec_name, sub.description
            FROM teacher_assignment ta
            INNER JOIN teacher t ON ta.teacher_id = t.ID
            LEFT JOIN section s ON ta.section_id = s.ID
            INNER JOIN subject sub ON ta.subject_id = sub.id
            WHERE ta.academic_year_id = %s 
                AND ta.is_subject_teacher = 1
                AND ta.subject_id > 0
                AND t.status = 'active'
        """, (selected_academic_year_id,))
        subject_assignments = cursor.fetchall()
        
        # Organize subject teachers by grade and subject
        for assignment in subject_assignments:
            grade_level = None
            for level, gid in GRADE_MAPPING.items():
                if gid == assignment['grade_id']:
                    grade_level = level
                    break
            
            if grade_level and assignment['description']:
                subject_name = assignment['description']
                if subject_name not in subject_teachers[grade_level]:
                    subject_teachers[grade_level][subject_name] = []
                if assignment['teacher_name'] not in subject_teachers[grade_level][subject_name]:
                    subject_teachers[grade_level][subject_name].append(assignment['teacher_name'])
    
    # Get sections with students for each grade
    total_sections_with_students = 0
    total_students = 0
    
    for grade_level, grade_id in GRADE_MAPPING.items():
        if selected_academic_year_id:
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
        
        for section in sections:
            section_name = section['sec_name'].strip()
            
            # Find room teacher from assignments
            room_teacher = 'Not assigned'
            
            if section_name in room_teachers[grade_level]:
                room_teacher = room_teachers[grade_level][section_name]['teacher_name']
            else:
                # Try case-insensitive match
                for key, assignment in room_teachers[grade_level].items():
                    if key.strip().lower() == section_name.lower():
                        room_teacher = assignment['teacher_name']
                        break
            
            grade_sections[grade_level].append({
                'sec_name': section_name,
                'student_count': section['student_count'],
                'room_teacher': room_teacher
            })
            total_students += section['student_count']
        
        total_sections_with_students += len(grade_sections[grade_level])
    
    cursor.close()
    conn.close()
    
    # Check if any sections exist
    has_any_sections = False
    for grade in grade_sections:
        if grade_sections[grade]:
            has_any_sections = True
            break
    
    # Calculate total subject teachers count for display
    total_subject_teachers = 0
    for grade_subjects in subject_teachers.values():
        for teachers_list in grade_subjects.values():
            total_subject_teachers += len(teachers_list)
    
    # Prepare ec_year_mapping list for template
    ec_year_mapping_list = list(EC_YEAR_MAPPING.values())
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <link rel="stylesheet" href="/static/css/core.css">
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Teacher Assignments by Section</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        
    </head>
    <body>
        <div class="container py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2 class="mb-0"><i class="fas fa-users me-2"></i>Teacher Assignments by Section</h2>
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
                            <p class="mt-2">1st to 8th Grade</p>
                            <div class="mt-2">
                                <span class="badge bg-info">Active Teachers: {{ teachers|length }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Navigation Tabs -->
            <ul class="nav nav-tabs mb-4" id="teacherTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="sections-tab" data-bs-toggle="tab" data-bs-target="#sections" type="button" role="tab">
                        <i class="fas fa-door-open me-2"></i>Sections & Room Teachers
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="subjects-tab" data-bs-toggle="tab" data-bs-target="#subjects" type="button" role="tab">
                        <i class="fas fa-book me-2"></i>Subject Teachers
                    </button>
                </li>
            </ul>
            
            <div class="tab-content" id="teacherTabsContent">
                <!-- Sections Tab -->
                <div class="tab-pane fade show active" id="sections" role="tabpanel">
                    {% if has_any_sections %}
                        <div class="row">
                            {% for grade_level in [1,2,3,4,5,6,7,8] %}
                                {% set sections = grade_sections[grade_level] %}
                                {% if sections %}
                                    {% set grade_student_count = 0 %}
                                    {% for s in sections %}
                                        {% set grade_student_count = grade_student_count + s.student_count %}
                                    {% endfor %}
                                    {% set has_students = grade_student_count > 0 %}
                                    <div class="col-md-6 col-lg-3 mb-4">
                                        <div class="grade-card h-100 {{ '' if has_students else 'zero-students' }}">
                                            <div class="grade-header grade-{{ grade_level }}">
                                                <h4 class="mb-0">
                                                    <i class="fas fa-graduation-cap me-2"></i>Grade {{ grade_level }}
                                                </h4>
                                                <div class="d-flex justify-content-between mt-2">
                                                    <small>
                                                        <i class="fas fa-door-open me-1"></i>{{ sections|length }} Sections
                                                    </small>
                                                    <small>
                                                        <i class="fas fa-user-graduate me-1"></i>{{ grade_student_count }} Students
                                                    </small>
                                                </div>
                                            </div>
                                            <div class="card-body p-0">
                                                <div class="list-group list-group-flush">
                                                    {% for section in sections %}
                                                        <div class="list-group-item">
                                                            <div class="d-flex justify-content-between align-items-start">
                                                                <div>
                                                                    <div class="section-name">
                                                                        <i class="fas fa-chalkboard me-2"></i>Section {{ section.sec_name }}
                                                                    </div>
                                                                    <div class="teacher-name mt-1 {{ 'not-assigned' if section.room_teacher == 'Not assigned' else 'assigned' }}">
                                                                        <i class="fas fa-user-tie me-1"></i>
                                                                        {{ section.room_teacher }}
                                                                        {% if section.room_teacher == 'Not assigned' %}
                                                                            <span class="badge bg-warning text-dark ms-2">No teacher assigned</span>
                                                                        {% endif %}
                                                                    </div>
                                                                </div>
                                                                <div class="text-end">
                                                                    <span class="badge bg-primary rounded-pill fs-6">{{ section.student_count }} Students</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    {% endfor %}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                {% endif %}
                            {% endfor %}
                        </div>
                    {% else %}
                        <div class="empty-state">
                            <i class="fas fa-door-open"></i>
                            <h4>No Sections Found</h4>
                            <p>There are currently no sections{% if selected_ec_year %} for the academic year {{ selected_display }}{% endif %}.</p>
                        </div>
                    {% endif %}
                </div>
                
                <!-- Subject Teachers Tab -->
                <div class="tab-pane fade" id="subjects" role="tabpanel">
                    {% if total_subject_teachers > 0 %}
                        <div class="row">
                            {% for grade_level in [1,2,3,4,5,6,7,8] %}
                                {% set subjects = subject_teachers[grade_level] %}
                                {% if subjects %}
                                    {% set subject_teacher_count = 0 %}
                                    {% for teachers_list in subjects.values() %}
                                        {% set subject_teacher_count = subject_teacher_count + teachers_list|length %}
                                    {% endfor %}
                                    <div class="col-md-6 col-lg-3 mb-4">
                                        <div class="grade-card h-100">
                                            <div class="grade-header grade-{{ grade_level }}">
                                                <h4 class="mb-0">
                                                    <i class="fas fa-graduation-cap me-2"></i>Grade {{ grade_level }}
                                                </h4>
                                                <div class="d-flex justify-content-between mt-2">
                                                    <small>
                                                        <i class="fas fa-book me-1"></i>{{ subjects.keys()|list|length }} Subjects
                                                    </small>
                                                    <small>
                                                        <i class="fas fa-chalkboard me-1"></i>{{ subject_teacher_count }} Teachers
                                                    </small>
                                                </div>
                                            </div>
                                            <div class="card-body p-0">
                                                <div class="list-group list-group-flush">
                                                    {% for subject, teachers in subjects.items() %}
                                                        <div class="list-group-item">
                                                            <div class="fw-bold mb-2">
                                                                <i class="fas fa-book-open me-2"></i>{{ subject }}
                                                            </div>
                                                            {% for teacher in teachers %}
                                                                <div class="subject-teacher ms-3">
                                                                    <i class="fas fa-user-tie me-1"></i>{{ teacher }}
                                                                </div>
                                                            {% endfor %}
                                                        </div>
                                                    {% endfor %}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                {% endif %}
                            {% endfor %}
                        </div>
                    {% else %}
                        <div class="empty-state">
                            <i class="fas fa-book"></i>
                            <h4>No Subject Teachers Assigned</h4>
                            <p>There are currently no subject teachers assigned to any grades for the selected academic year.</p>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        
        <script src="/static/js/core.js"></script>
</body>
    </html>
    ''',
    available_ec_years=available_ec_years,
    selected_ec_year=selected_ec_year,
    selected_display=selected_display,
    ec_year_mapping=ec_year_mapping_list,
    teachers=teachers,
    total_sections_with_students=total_sections_with_students,
    total_students=total_students,
    has_any_sections=has_any_sections,
    grade_sections=grade_sections,
    subject_teachers=subject_teachers,
    total_subject_teachers=total_subject_teachers
    )