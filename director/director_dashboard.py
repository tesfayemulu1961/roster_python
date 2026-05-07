# ==============================================
# Director Dashboard - Complete Python Conversion
# Converted from director_dashboard.php
# ==============================================

from flask import Blueprint, render_template_string, session, redirect
from functools import wraps
import mysql.connector
from datetime import datetime

# Create blueprint
director_dashboard_bp = Blueprint('director_dashboard', __name__, url_prefix='/director')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        allowed_types = ['director']
        if session.get('user_type') not in allowed_types:
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

@director_dashboard_bp.route('/director_dashboard')
@login_required
def director_dashboard():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get director details from admin_staff table
        cursor.execute("SELECT * FROM admin_staff WHERE ID = %s AND role = 'director'", (session.get('reference_id', 1),))
        director = cursor.fetchone()
        
        if not director:
            # Try to get any director
            cursor.execute("SELECT * FROM admin_staff WHERE role = 'director' LIMIT 1")
            director = cursor.fetchone()
        
        # Get last login time
        cursor.execute("SELECT last_login FROM users WHERE user_id = %s", (session['user_id'],))
        last_login_result = cursor.fetchone()
        last_login = last_login_result['last_login'] if last_login_result else None
        
        # Get total staff
        cursor.execute("SELECT COUNT(*) as total_staff FROM admin_staff")
        total_staff = cursor.fetchone()['total_staff'] or 0
        
        # Get total teachers
        cursor.execute("SELECT COUNT(*) as total_teachers FROM teacher_assignment WHERE academic_year_id = 3")
        total_teachers = cursor.fetchone()['total_teachers'] or 0
        
        # Get total grades
        cursor.execute("SELECT COUNT(*) as total_grades FROM grade WHERE ID IN (5,6,7,8,9,10,11,12)")
        total_grades = cursor.fetchone()['total_grades'] or 0
        
        # Get total sections
        cursor.execute("""
            SELECT COUNT(DISTINCT s.ID) as total_sections 
            FROM section s
            JOIN student st ON s.ID = st.section_id
            WHERE s.grade_id IN (5,6,7,8,9,10,11,12)
            AND s.sec_name IN ('A', 'B', 'C', 'D')
        """)
        total_sections = cursor.fetchone()['total_sections'] or 0
        
        # Get total students
        cursor.execute("SELECT COUNT(*) as total_students FROM enrollment WHERE academic_year_id = 3")
        total_students = cursor.fetchone()['total_students'] or 0
        
    except Exception as e:
        print(f"Database error: {e}")
        director = {'full_name': session.get('username', 'Director'), 'phone': 'N/A', 'photo': None}
        last_login = None
        total_staff = total_teachers = total_grades = total_sections = total_students = 0
    
    cursor.close()
    conn.close()
    
    director_name = director['full_name'] if director else session.get('username', 'Director')
    director_first_name = director_name.split()[0] if director_name else session.get('username', 'Director')
    director_phone = director['phone'] if director else 'N/A'
    director_photo = director.get('photo') if director else None
    
    last_login_str = "First login"
    if last_login:
        if isinstance(last_login, datetime):
            last_login_str = last_login.strftime('%b %d, %Y at %I:%M %p')
        else:
            last_login_str = str(last_login)
    
    # Convert photo to base64 if exists
    photo_html = ''
    if director_photo:
        import base64
        photo_base64 = base64.b64encode(director_photo).decode('utf-8')
        photo_html = f'<img src="data:image/jpeg;base64,{photo_base64}" alt="Director Photo" class="user-avatar" style="width:40px;height:40px;border-radius:50%;object-fit:cover;margin-right:10px;">'
    else:
        photo_html = '<div class="user-avatar bg-secondary d-flex align-items-center justify-content-center" style="width:40px;height:40px;border-radius:50%;background-color:#6c757d;margin-right:10px;"><i class="fas fa-user text-white"></i></div>'
    
    DASHBOARD_HTML = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <link rel="stylesheet" href="/static/css/core.css">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>School Director Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/director_dashboard.css">
</head>
    <body>
        <header class="header">
            <div class="container d-flex justify-content-between align-items-center">
                <h3 class="mb-0"><i class="fas fa-school"></i> School Director Dashboard</h3>
                <div class="d-flex align-items-center">
                    <span class="me-3">Welcome, {director_first_name}!</span>
                    <a href="/logout" class="btn btn-danger btn-sm">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </a>
                </div>
            </div>
        </header>
        
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container-fluid">
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/director/director_dashboard">
                                <i class="fas fa-home"></i> Dashboard
                            </a>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="schoolMgtDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-school"></i> School Mgt
                            </a>
                            <ul class="dropdown-menu">
                                <li class="dropdown-submenu">
                                    <a class="dropdown-item dropdown-toggle" href="#">Academic Structure</a>
                                    <ul class="dropdown-menu">
                                        <li><a class="dropdown-item" href="/director/insert_grade">Insert Grade</a></li>
                                        <li><a class="dropdown-item" href="/director/view_grade">View Grades</a></li>
                                        <li><a class="dropdown-item" href="/director/insert_section">Insert Section</a></li>
                                        <li><a class="dropdown-item" href="/director/view_section">View Sections</a></li>
                                        <li><a class="dropdown-item" href="/director/insert_class">Insert Class</a></li>
                                        <li><a class="dropdown-item" href="/director/view_class">View Classes</a></li>
                                        <li><a class="dropdown-item" href="/director/insert_subject">Insert Subject</a></li>
                                        <li><a class="dropdown-item" href="/director/view_subject">View Subjects</a></li>
                                    </ul>
                                </li>
                                <li class="dropdown-submenu">
                                    <a class="dropdown-item dropdown-toggle" href="#">Operations</a>
                                    <ul class="dropdown-menu">
                                        <li><a class="dropdown-item" href="/director/insert_room">Insert Room</a></li>
                                        <li><a class="dropdown-item" href="/director/view_room">View Rooms</a></li>
                                        <li><a class="dropdown-item" href="/director/attendance_tracking">Attendance Tracking</a></li>
                                    </ul>
                                </li>
                            </ul>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="studentDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-user-graduate"></i> Students
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="/director/insert_student_parent">Register Students & Parents</a></li>
                                <li><a class="dropdown-item" href="/director/view_student_parent_paginated">View Students & Parents</a></li>
                            </ul>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="teacherDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-chalkboard-teacher"></i> Teachers
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="/director/upload">Upload Files</a></li>
                                <li><a class="dropdown-item" href="/director/materials">Download Files</a></li>
                                <li><a class="dropdown-item" href="/director/insert_teacher">Teacher Registration</a></li>
                                <li><a class="dropdown-item" href="/director/view_teacher">View Teachers</a></li>
                                <li><a class="dropdown-item" href="/director/insert_teacher_assignment">Assign Teachers</a></li>
                                <li><a class="dropdown-item" href="/director/view_teacher_assignment">View Assigned Teachers</a></li>
                                <li><a class="dropdown-item" href="/director/view_room_teachers">View Room Teachers</a></li>
                                <li><a class="dropdown-item" href="/director/view_subject_teachers">View Subject Teachers</a></li>
                            </ul>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="scoresDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-clipboard-list"></i> Subject Scores
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="/director/insert_student_scores">Insert Scores</a></li>
                                <li><a class="dropdown-item" href="/director/insert_assessment">Insert Assessment</a></li>
                                <li><a class="dropdown-item" href="/director/view_assessment">View Assessments</a></li>
                                <li><a class="dropdown-item" href="/director/view_transfer_sheet">View Transfersheet</a></li>
                                <li><a class="dropdown-item" href="/director/excel_import">Excel Import</a></li>
                            </ul>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="analysisDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-chart-bar"></i> Result Analysis
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="/director/view_student_scores">View Semester Scores</a></li>
                                <li><a class="dropdown-item" href="/director/view_student_average_scores">View Average Scores</a></li>
                                <li><a class="dropdown-item" href="/director/view_student_roster">View Roster</a></li>
                                <li><a class="dropdown-item" href="/director/report_card">View Report Card</a></li>
                                <li><a class="dropdown-item" href="/director/semester_analysis">Semester Analysis</a></li>
                                <li><a class="dropdown-item" href="/director/semester_average_analysis">Semester Average Analysis</a></li>
                                <li><a class="dropdown-item" href="/director/annual_average_analysis">Annual Average Analysis</a></li>
                                <li><a class="dropdown-item" href="/director/semester_and_average_analysis">Semester & Average Summary</a></li>
                                <li><a class="dropdown-item" href="/director/subject_based_summary_analysis">Subject Based Summary</a></li>
                                <li><a class="dropdown-item" href="/director/grade_level_analysis">Grade-level Analysis</a></li>
                                <li><a class="dropdown-item" href="/director/grade_level_summary_analysis">Grade-level Summary</a></li>
                            </ul>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="adminDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-cog"></i> Administration
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="/director/insert_admin_staff">Insert Staff</a></li>
                                <li><a class="dropdown-item" href="/director/view_admin_staff">View Staff</a></li>
                                <li><a class="dropdown-item" href="/director/school_policies">School Policies</a></li>
                                <li><a class="dropdown-item" href="/director/calendar">School Calendar</a></li>
                                <li><a class="dropdown-item" href="/director/staff_management">Staff Management</a></li>
                                <li><a class="dropdown-item" href="/director/inventory_management">Inventory Management</a></li>
                            </ul>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-users"></i> Users
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="/director/insert_users">Add New User</a></li>
                                <li><a class="dropdown-item" href="/director/manage_users">Manage Users</a></li>
                                <li><a class="dropdown-item" href="/director/view_users">View Users</a></li>
                                <li><a class="dropdown-item" href="/director/user_permissions">User Permissions</a></li>
                                <li><a class="dropdown-item" href="/director/activity_log">Activity Log</a></li>
                                <li><a class="dropdown-item" href="/director/view_login_attempts">View Login Attempts</a></li>
                            </ul>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="academicYearDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-calendar"></i> Academic Year
                            </a>
                            <ul class="dropdown-menu dropdown-menu-end">
                                <li><a class="dropdown-item" href="/director/insert_academic_year">Add New Academic Year</a></li>
                                <li><a class="dropdown-item" href="/director/view_academic_year">View Academic Years</a></li>
                                <li><a class="dropdown-item" href="/director/academic_year_converter">Convert Academic Year</a></li>
                                <li><a class="dropdown-item" href="/director/view_graduated_students">View Graduated Students</a></li>
                                <li><a class="dropdown-item" href="/director/view_student_enrollment">View Student Enrollment</a></li>
                                <li><a class="dropdown-item" href="/director/new_students">New Students</a></li>
                            </ul>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        
        <main class="container main-content">
            <div class="row">
                <div class="col-md-6">
                    <div class="dashboard-card">
                        <h3><i class="fas fa-user-tie"></i> Director Profile</h3>
                        <div class="d-flex align-items-center mb-3">
                            {photo_html}
                            <div>
                                <h5 class="mb-0">{director_name}</h5>
                                <small class="text-muted">School Director</small>
                            </div>
                        </div>
                        <p><strong>Phone:</strong> {director_phone}</p>
                        <p><strong>Last Login:</strong> {last_login_str}</p>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="dashboard-card">
                        <h3><i class="fas fa-chart-pie"></i> School Statistics</h3>
                        <div class="row mt-3">
                            <div class="col-md-6">
                                <div class="stat-card">
                                    <h5>Total Staff</h5>
                                    <h4>{total_staff:,}</h4>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="stat-card">
                                    <h5>Total Teachers</h5>
                                    <h4>{total_teachers:,} <a href="/director/teacher_category" class="btn btn-sm btn-outline-primary">Details →</a></h4>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="stat-card">
                                    <h5>Total Grades</h5>
                                    <h4>{total_grades:,}</h4>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="stat-card">
                                    <h5>Total Sections</h5>
                                    <h4>{total_sections:,} <a href="/director/active_sections" class="btn btn-sm btn-outline-primary">Details →</a></h4>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="stat-card">
                                    <h5>Total Students</h5>
                                    <h4>{total_students:,} <a href="/director/student_statistics" class="btn btn-sm btn-outline-primary">Details →</a></h4>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-12">
                    <div class="dashboard-card">
                        <h3 class="mb-3"><i class="fas fa-bolt"></i> Quick Actions</h3>
                        <div class="row">
                            <div class="col-md-3 col-6 mb-3">
                                <a href="/director/insert_student_parent" class="btn btn-primary quick-action-btn">
                                    <i class="fas fa-user-plus"></i> Register Student
                                </a>
                            </div>
                            <div class="col-md-3 col-6 mb-3">
                                <a href="/director/insert_teacher" class="btn btn-success quick-action-btn">
                                    <i class="fas fa-chalkboard-teacher"></i> Add Teacher
                                </a>
                            </div>
                            <div class="col-md-3 col-6 mb-3">
                                <a href="/director/school_reports" class="btn btn-info quick-action-btn">
                                    <i class="fas fa-file-alt"></i> School Reports
                                </a>
                            </div>
                            <div class="col-md-3 col-6 mb-3">
                                <a href="/director/insert_users" class="btn btn-warning quick-action-btn">
                                    <i class="fas fa-user-plus"></i> Create User
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
       <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="/static/js/director_dashboard.js"></script>
        <script src="/static/js/core.js"></script>
</body>
    </html>
    '''
    
    return DASHBOARD_HTML


# ============== Placeholder routes for all menu items ==============
#@director_dashboard_bp.route('/insert_grade')
#@login_required
#def insert_grade():
    #return "<h2>Insert Grade</h2><p>Coming soon: Insert Grade functionality</p><a href='/director/director_dashboard'>Back to Dashboard</a>"

#@director_dashboard_bp.route('/view_grade')
#@login_required
#def view_grade():
    #return "<h2>View Grades</h2><p>Coming soon: View Grades functionality</p><a href='/director/director_dashboard'>Back to Dashboard</a>"

#@director_dashboard_bp.route('/insert_section')
#@login_required
#def insert_section():
    #return "<h2>Insert Section</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/view_section')
#@login_required
#def view_section():
    #return "<h2>View Sections</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/insert_class')
#@login_required
#def insert_class():
    #return "<h2>Insert Class</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/view_class')
#@login_required
#def view_class():
   # return "<h2>View Classes</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/insert_subject')
#@login_required
#def insert_subject():
    #return "<h2>Insert Subject</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/view_subject')
#@login_required
#def view_subject():
    #return "<h2>View Subjects</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

@director_dashboard_bp.route('/insert_room')
@login_required
def insert_room():
    return "<h2>Insert Room</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

@director_dashboard_bp.route('/view_room')
@login_required
def view_room():
    return "<h2>View Rooms</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

@director_dashboard_bp.route('/attendance_tracking')
@login_required
def attendance_tracking():
    return "<h2>Attendance Tracking</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/view_student_scores')
##@login_required
#def view_student_scores():
   # return "<h2>View Semester Scores</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/view_student_average_scores')
#@login_required
#def view_student_average_scores():
    #return "<h2>View Average Scores</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/view_student_roster')
#@login_required
#def view_student_roster():
    #return "<h2>View Roster</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/report_card')
#@login_required
#def report_card():
    #return "<h2>View Report Card</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/semester_analysis')
#@login_required
#def semester_analysis():
    #return "<h2>Semester Analysis</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/semester_average_analysis')
#@login_required
#def semester_average_analysis():
    #return "<h2>Semester Average Analysis</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/annual_average_analysis')
#@login_required
#def annual_average_analysis():
    #return "<h2>Annual Average Analysis</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/semester_and_average_analysis')
#@login_required
#def semester_and_average_analysis():
    #return "<h2>Semester & Average Summary</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/subject_based_summary_analysis')
#@login_required
#def subject_based_summary_analysis():
    #return "<h2>Subject Based Summary</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/grade_level_analysis')
#@login_required
#def grade_level_analysis():
    #return "<h2>Grade-level Analysis</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/grade_level_summary_analysis')
#@login_required
#def grade_level_summary_analysis():
    #return "<h2>Grade-level Summary</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/insert_admin_staff')
#@login_required
#def insert_admin_staff():
    #return "<h2>Insert Staff</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/view_admin_staff')
#@login_required
#def view_admin_staff():
    #return "<h2>View Staff</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

@director_dashboard_bp.route('/school_policies')
@login_required
def school_policies():
    return "<h2>School Policies</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

@director_dashboard_bp.route('/calendar')
@login_required
def calendar():
    return "<h2>School Calendar</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

@director_dashboard_bp.route('/staff_management')
@login_required
def staff_management():
    return "<h2>Staff Management</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

@director_dashboard_bp.route('/inventory_management')
@login_required
def inventory_management():
    return "<h2>Inventory Management</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/insert_users')
#@login_required
#def insert_users():
    #return "<h2>Add New User</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/manage_users')
#@login_required
#def manage_users():
    #return "<h2>Manage Users</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/view_users')
#@login_required
#def view_users():
    #return "<h2>View Users</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/user_permissions')
#@login_required
#def user_permissions():
    #return "<h2>User Permissions</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/activity_log')
#@login_required
#def activity_log():
    #return "<h2>Activity Log</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/view_login_attempts')
#@login_required
#def view_login_attempts():
    #return "<h2>View Login Attempts</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/insert_academic_year')
#@login_required
#def insert_academic_year():
    #return "<h2>Add Academic Year</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/view_academic_year')
#@login_required
#def view_academic_year():
   # return "<h2>View Academic Years</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/academic_year_converter')
#@login_required
#def academic_year_converter():
    #return "<h2>Convert Academic Year</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/view_graduated_students')
#@login_required
#def view_graduated_students():
    #return "<h2>View Graduated Students</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/view_student_enrollment')
#@login_required
#def view_student_enrollment():
    r#eturn "<h2>View Student Enrollment</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/new_students')
#@login_required
#def new_students():
    #return "<h2>New Students</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/teacher_category')
#@login_required
#def teacher_category():
 #  return "<h2>Teacher Category</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

#@director_dashboard_bp.route('/active_sections')
#@login_required
#def active_sections():
   # return "<h2>Active Sections</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"

# @director_dashboard_bp.route('/student_statistics')
# @login_required
# def student_statistics():
#     return "<h2>Student Statistics</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"
@director_dashboard_bp.route('/school_reports')
@login_required
def school_reports():
    return "<h2>School Reports</h2><p>Coming soon</p><a href='/director/director_dashboard'>Back</a>"