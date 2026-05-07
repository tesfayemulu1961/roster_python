from flask import Blueprint, session, redirect, render_template_string, request, url_for
from functools import wraps
from datetime import datetime
import mysql.connector
import base64

# Create blueprint
grade_6A_rt_bp = Blueprint('grade_6A_rt', __name__, url_prefix='/room_teacher/grade_6A')

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db():
    return mysql.connector.connect(**db_config)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        if session.get('user_type') != 'room teacher grade 6th A':
            return redirect('/unauthorized')
        return f(*args, **kwargs)
    return decorated_function

@grade_6A_rt_bp.route('/grade_6A_rt_dashboard')
@login_required
def grade_6A_rt_dashboard():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get teacher details
    cursor.execute("SELECT * FROM teacher WHERE ID = %s", (session.get('reference_id', 1),))
    room_teacher = cursor.fetchone()
    
    # Get last login time
    cursor.execute("SELECT last_login FROM users WHERE user_id = %s", (session['user_id'],))
    last_login_result = cursor.fetchone()
    last_login = last_login_result['last_login'] if last_login_result else None
    
    # Get total students
    cursor.execute("SELECT COUNT(*) as total_students FROM enrollment WHERE grade_id = 10 AND section_id = 1 AND academic_year_id = 3")
    total_students_result = cursor.fetchone()
    total_students = total_students_result['total_students'] if total_students_result else 0
    
    cursor.close()
    conn.close()
    
    # Prepare teacher data
    teacher_name = room_teacher['name'] if room_teacher else session.get('username')
    teacher_first_name = teacher_name.split()[0] if teacher_name else session.get('username')
    teacher_email = room_teacher['email'] if room_teacher else 'N/A'
    teacher_phone = room_teacher['phone'] if room_teacher else 'N/A'
    
    # Handle teacher photo
    teacher_photo = None
    if room_teacher and room_teacher.get('photo'):
        teacher_photo = base64.b64encode(room_teacher['photo']).decode('utf-8')
    
    last_login_str = "First login"
    if last_login:
        if isinstance(last_login, datetime):
            last_login_str = last_login.strftime('%b %d, %Y at %I:%M %p')
        else:
            last_login_str = str(last_login)
    
    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <link rel="stylesheet" href="/static/css/core.css">
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Grade 6th A Room Teacher Dashboard</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css">
        
    </head>
    <body>
        <!-- Header Section -->
        <header class="header">
            <div class="container d-flex justify-content-between align-items-center">
                <h3 class="mb-0">Grade 6th A Room Teacher Dashboard</h3>
                <div class="user-info">
                    <span>Welcome, {teacher_first_name}!</span>
                    <a href="/logout" class="logout-btn">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </a>
                </div>
            </div>
        </header>
        
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container">
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/room_teacher/grade_6A/grade_6A_rt_dashboard">
                                <i class="fas fa-home"></i> Dashboard
                            </a>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="teachingMaterialsDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-users"></i> Teaching Materials
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#" onclick="alert('Upload Files - Coming Soon')">Upload Files</a></li>
                                <li><a class="dropdown-item" href="#" onclick="alert('Download Files - Coming Soon')">Download Files</a></li>
                            </ul>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="classManagementDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-users"></i> Class Management
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#" onclick="alert('My Class - Coming Soon')">My Class</a></li>
                                <li><a class="dropdown-item" href="#" onclick="alert('Attendance - Coming Soon')">Attendance</a></li>
                            </ul>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="gradesDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-graduation-cap"></i> Assessment
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#" onclick="alert('Insert Assessment 1 - Coming Soon')">Insert Assessment 1</a></li>
                                <li><a class="dropdown-item" href="#" onclick="alert('Insert Assessment 2 - Coming Soon')">Insert Assessment 2</a></li>
                                <li><a class="dropdown-item" href="#" onclick="alert('View Assessment - Coming Soon')">View Assessment</a></li>
                            </ul>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="scoresDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-graduation-cap"></i> Insert Scores
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#" onclick="alert('Insert Transfersheet - Coming Soon')">Insert Transfersheet</a></li>
                                <li><a class="dropdown-item" href="#" onclick="alert('Insert Scores - Coming Soon')">Insert Scores</a></li>
                            </ul>
                        </li>
                        
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="analysisDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-chart-bar"></i> Result Analysis
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#" onclick="alert('View Transfer Sheet - Coming Soon')">View Transfer Sheet</a></li>
                                <li><a class="dropdown-item" href="#" onclick="alert('View Semester and Average Scores - Coming Soon')">View Semester and Average Scores</a></li>
                                <li><a class="dropdown-item" href="#" onclick="alert('View Average Scores - Coming Soon')">View Average Scores</a></li>
                                <li><a class="dropdown-item" href="#" onclick="alert('View Student Roster - Coming Soon')">View Student Roster</a></li>
                                <li><a class="dropdown-item" href="#" onclick="alert('Semester and Average Analysis - Coming Soon')">Semester and Average Analysis</a></li>
                                <li><a class="dropdown-item" href="#" onclick="alert('Annual Average Analysis - Coming Soon')">Annual Average Analysis</a></li>
                            </ul>
                        </li>
                        
                        <li class="nav-item">
                            <a class="nav-link" href="#" onclick="alert('Announcements - Coming Soon')">
                                <i class="fas fa-bullhorn"></i> Announcements
                            </a>
                        </li>
                        
                        <li class="nav-item">
                            <a class="nav-link" href="#" onclick="alert('Parent Communication - Coming Soon')">
                                <i class="fas fa-envelope"></i> Parent Communication
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        
        <!-- Main Content -->
        <main class="container main-content">
            <div class="row">
                <div class="col-md-6">
                    <div class="dashboard-card">
                        <h3><i class="fas fa-user-tie"></i> Teacher Profile</h3>
                        <div class="d-flex align-items-center mb-3">
                            {'<img src="data:image/jpeg;base64,' + teacher_photo + '" alt="Teacher Photo" class="user-avatar">' if teacher_photo else '<div class="user-avatar bg-secondary d-flex align-items-center justify-content-center"><i class="fas fa-user text-white"></i></div>'}
                            <div>
                                <h5 class="mb-0">{teacher_name}</h5>
                                <small class="text-muted">Grade 6th A Room Teacher</small>
                            </div>
                        </div>
                        <p><strong>Email:</strong> {teacher_email}</p>
                        <p><strong>Phone:</strong> {teacher_phone}</p>
                        <p><strong>Last Login:</strong> {last_login_str}</p>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="dashboard-card">
                        <h3><i class="fas fa-info-circle"></i> Class Information</h3>
                        <div class="mb-3">
                            <h5>Grade 6th A</h5>
                            <p><strong>Room Teacher:</strong> {teacher_name}</p>
                            <p><strong>School Year:</strong> 2025-2026</p>
                        </div>
                        
                        <div class="stat-card">
                            <div class="d-flex align-items-center justify-content-between">
                                <div class="d-flex align-items-center gap-3">
                                    <h5 class="mb-0">Total Students:</h5>
                                    <h4 class="mb-0">{total_students:,}</h4>
                                </div>
                                <a href="#" onclick="alert('Student Statistics - Coming Soon')" class="btn btn-sm btn-outline-primary">Details →</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-12">
                    <div class="dashboard-card">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h3 class="mb-0"><i class="fas fa-tasks"></i> Quick Actions</h3>
                        </div>
                        <div class="row">
                            <div class="col-md-3 col-6 mb-3">
                                <a href="#" onclick="alert('My Class - Coming Soon')" class="btn btn-primary w-100">
                                    <i class="fas fa-users"></i> My Class
                                </a>
                            </div>
                            <div class="col-md-3 col-6 mb-3">
                                <a href="#" onclick="alert('Attendance - Coming Soon')" class="btn btn-success w-100">
                                    <i class="fas fa-clipboard-check"></i> Attendance
                                </a>
                            </div>
                            <div class="col-md-3 col-6 mb-3">
                                <a href="#" onclick="alert('Semester Grades - Coming Soon')" class="btn btn-info w-100">
                                    <i class="fas fa-graduation-cap"></i> Semester Grades
                                </a>
                            </div>
                            <div class="col-md-3 col-6 mb-3">
                                <a href="#" onclick="alert('Parent Messages - Coming Soon')" class="btn btn-warning w-100">
                                    <i class="fas fa-envelope"></i> Parent Messages
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        
        <script src="/static/js/core.js"></script>
</body>
    </html>
    ''')