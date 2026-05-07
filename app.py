from flask import Flask, render_template_string, session, redirect, request
from datetime import datetime
import mysql.connector
import sys
import os
import re
import importlib.util

# Import the log_activity function from activity_log blueprint
from director.activity_log import log_activity

# Add the current directory to path
sys.path.insert(0, os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db():
    return mysql.connector.connect(**db_config)

# ============== IMPORT AND REGISTER ALL DASHBOARD BLUEPRINTS ==============

# Import Director Dashboard
try:
    from director.director_dashboard import director_dashboard_bp
    app.register_blueprint(director_dashboard_bp)
    print("✓ Director dashboard registered")
    print("  → URL: /director/director_dashboard")
except Exception as e:
    print(f"✗ Error registering director dashboard: {e}")
    # ============== ADD STUDENT STATISTICS BLUEPRINT HERE ==============
# Import Student Statistics Blueprint
try:
    from director.student_statistics import director_student_statistics
    app.register_blueprint(director_student_statistics)
    print("✅ Student Statistics Blueprint registered")
    print("  → URL: /director/student_statistics")
except Exception as e:
    print(f"❌ Error registering student statistics: {e}")
    
    # Import Teacher Category Blueprint
try:
    from director.teacher_category import director_teacher_category
    app.register_blueprint(director_teacher_category)
    print("✅ Teacher Category Blueprint registered")
    print("  → URL: /director/teacher_category")
except Exception as e:
    print(f"❌ Error registering teacher category: {e}")
    
    # Import Active Sections
try:
    from director.active_sections import director_active_sections
    app.register_blueprint(director_active_sections)
    print("✅ Active Sections Blueprint registered")
    print("  → URL: /director/active_sections")
except Exception as e:
    print(f"❌ Error registering active sections: {e}")
    
# Import Insert Grade
try:
    from director.insert_grade import director_insert_grade
    app.register_blueprint(director_insert_grade)
    print("✅ Insert Grade Blueprint registered")
    print("  → URL: /director/insert_grade")
except Exception as e:
    print(f"❌ Error registering insert grade: {e}")
    
    # Import View Grade
try:
    from director.view_grade import director_view_grade
    app.register_blueprint(director_view_grade)
    print("✅ View Grade Blueprint registered")
except Exception as e:
    print(f"❌ Error: {e}")

# Import Insert Section
try:
    from director.insert_section import director_insert_section
    app.register_blueprint(director_insert_section)
    print("✅ Insert Section Blueprint registered")
except Exception as e:
    print(f"❌ Error: {e}")

# Import View Section
try:
    from director.view_section import director_view_section
    app.register_blueprint(director_view_section)
    print("✅ View Section Blueprint registered")
except Exception as e:
    print(f"❌ Error: {e}")

# Import Insert Class
try:
    from director.insert_class import director_insert_class
    app.register_blueprint(director_insert_class)
    print("✅ Insert Class Blueprint registered")
except Exception as e:
    print(f"❌ Error: {e}")

# Import View Class
try:
    from director.view_class import director_view_class
    app.register_blueprint(director_view_class)
    print("✅ View Class Blueprint registered")
except Exception as e:
    print(f"❌ Error: {e}")

# Import Insert Subject
try:
    from director.insert_subject import director_insert_subject
    app.register_blueprint(director_insert_subject)
    print("✅ Insert Subject Blueprint registered")
except Exception as e:
    print(f"❌ Error: {e}")

# Import View Subject
try:
    from director.view_subject import director_view_subject
    app.register_blueprint(director_view_subject)
    print("✅ View Subject Blueprint registered")
except Exception as e:
    print(f"❌ Error: {e}")
    
# Import View Admin Staff
try:
    from director.view_admin_staff import view_admin_staff_bp
    app.register_blueprint(view_admin_staff_bp)
    print("✅ View Admin Staff registered")
    print("  → URL: /director/view_admin_staff")
except Exception as e:
    print(f"❌ View Admin Staff error: {e}")
    import traceback
    traceback.print_exc()
    
   # Import Insert Student Parent
try:
    from director.insert_student_parent import insert_student_parent_bp
    app.register_blueprint(insert_student_parent_bp)
    print("✅ Insert Student Parent registered")
    print("  → URL: /director/insert_student_parent")
except Exception as e:
    print(f"❌ Insert Student Parent error: {e}")
    
    
# Import View Student & Parent Paginated
try:
    from director.view_student_parent_paginated import view_student_parent_bp
    app.register_blueprint(view_student_parent_bp)
    print("✅ View Student & Parent Paginated registered")
    print("  → URL: /director/view_student_parent_paginated")
except Exception as e:
    print(f"❌ Error: {e}")
    
    # Import Upload
try:
    from director.upload import director_upload
    app.register_blueprint(director_upload)
    print("✅ Upload Blueprint registered")
except Exception as e:
    print(f"❌ Upload error: {e}")

# Import Materials
try:
    from director.materials import director_materials
    app.register_blueprint(director_materials)
    print("✅ Materials Blueprint registered")
except Exception as e:
    print(f"❌ Materials error: {e}")

# Import Insert Teacher
try:
    from director.insert_teacher import director_insert_teacher
    app.register_blueprint(director_insert_teacher)
    print("✅ Insert Teacher registered")
except Exception as e:
    print(f"❌ Insert Teacher error: {e}")

# Import View Teacher
try:
    from director.view_teacher import director_view_teacher
    app.register_blueprint(director_view_teacher)
    print("✅ View Teacher registered")
except Exception as e:
    print(f"❌ View Teacher error: {e}")

# Import Insert Teacher Assignment
try:
    from director.insert_teacher_assignment import director_teacher_assignment
    app.register_blueprint(director_teacher_assignment)
    print("✅ Insert Teacher Assignment registered")
except Exception as e:
    print(f"❌ Insert Teacher Assignment error: {e}")

# Import View Teacher Assignment
try:
    from director.view_teacher_assignment import director_view_teacher_assignment
    app.register_blueprint(director_view_teacher_assignment)
    print("✅ View Teacher Assignment registered")
except Exception as e:
    print(f"❌ View Teacher Assignment error: {e}")

# Import View Room Teachers
try:
    from director.view_room_teachers import director_view_room_teachers
    app.register_blueprint(director_view_room_teachers)
    print("✅ View Room Teachers registered")
except Exception as e:
    print(f"❌ View Room Teachers error: {e}")

# Import View Subject Teachers
try:
    from director.view_subject_teachers import director_view_subject_teachers
    app.register_blueprint(director_view_subject_teachers)
    print("✅ View Subject Teachers registered")
except Exception as e:
    print(f"❌ View Subject Teachers error: {e}")
    
    # Import Insert Student Scores
try:
    from director.insert_student_scores import director_insert_student_scores
    app.register_blueprint(director_insert_student_scores)
    print("✅ Insert Student Scores registered")
except Exception as e:
    print(f"❌ Insert Student Scores error: {e}")

# Import Insert Assessment
try:
    from director.insert_assessment import director_insert_assessment
    app.register_blueprint(director_insert_assessment)
    print("✅ Insert Assessment registered")
except Exception as e:
    print(f"❌ Insert Assessment error: {e}")

# Import View Assessment
try:
    from director.view_assessment import director_view_assessment
    app.register_blueprint(director_view_assessment)
    print("✅ View Assessment registered")
except Exception as e:
    print(f"❌ View Assessment error: {e}")

# Import View Transfer Sheet
try:
    from director.view_transfer_sheet import director_view_transfer_sheet
    app.register_blueprint(director_view_transfer_sheet)
    print("✅ View Transfer Sheet registered")
except Exception as e:
    print(f"❌ View Transfer Sheet error: {e}")

# Import Excel Import
try:
    from director.excel_import import director_excel_import
    app.register_blueprint(director_excel_import)
    print("✅ Excel Import registered")
except Exception as e:
    print(f"❌ Excel Import error: {e}")
    
    # Import View Student Scores
try:
    from director.view_student_scores import director_view_student_scores
    app.register_blueprint(director_view_student_scores)
    print("✅ View Student Scores registered")
except Exception as e:
    print(f"❌ View Student Scores error: {e}")

# Import View Student Average Scores
try:
    from director.view_student_average_scores import director_view_student_average_scores
    app.register_blueprint(director_view_student_average_scores)
    print("✅ View Student Average Scores registered")
except Exception as e:
    print(f"❌ View Student Average Scores error: {e}")

# Import View Student Roster
try:
    from director.view_student_roster import director_view_student_roster
    app.register_blueprint(director_view_student_roster)
    print("✅ View Student Roster registered")
except Exception as e:
    print(f"❌ View Student Roster error: {e}")
    
    # Import Report Card
try:
    from director.report_card import director_report_card
    app.register_blueprint(director_report_card)
    print("✅ Report Card registered")
except Exception as e:
    print(f"❌ Report Card error: {e}")
    # Import Semester Analysis
try:
    from director.semester_analysis import director_semester_analysis
    app.register_blueprint(director_semester_analysis)
    print("✅ Semester Analysis registered")
except Exception as e:
    print(f"❌ Semester Analysis error: {e}")
    
    # Import Semester Analysis
try:
    from director.semester_average_analysis import director_semester_average_analysis
    app.register_blueprint(director_semester_average_analysis)
    print("✅ semester_average_analysis registered")
except Exception as e:
    print(f"❌ semester_average_analysis error: {e}")
    
    # Import Annual Average Analysis
try:
    from director.annual_average_analysis import director_annual_average_analysis
    app.register_blueprint(director_annual_average_analysis)
    print("✅ Annual Average Analysis registered")
except Exception as e:
    print(f"❌ Annual Average Analysis error: {e}")
    
    # Import Semester and Average Analysis
try:
    from director.semester_and_average_analysis import director_semester_and_average_analysis
    app.register_blueprint(director_semester_and_average_analysis)
    print("✅ Semester and Average Analysis registered")
except Exception as e:
    print(f"❌ Semester and Average Analysis error: {e}")
       
        # Import Annual Average Analysis
try:
    from director.subject_based_summary_analysis import director_subject_based_summary_analysis
    app.register_blueprint(director_subject_based_summary_analysis)
    print("✅ Subject Based Summary Analysis")
except Exception as e:
    print(f"❌ Subject Based Summary Analysis error: {e}")
    
    # Import Grade Level Analysis
try:
    from director.grade_level_analysis import grade_level_analysis_bp
    app.register_blueprint(grade_level_analysis_bp)
    print("✅ Grade Level Analysis")
except Exception as e:
    print(f"❌ Grade Level Analysis error: {e}")
    
    # Import Grade Level Summary Analysis
try:
    from director.grade_level_summary_analysis import grade_level_summary_bp
    app.register_blueprint(grade_level_summary_bp)
    print("✅ Grade Level Summary Analysis")
except Exception as e:
    print(f"❌ Grade Level Summary Analysis error: {e}")
    
    # Import Insert Admin Staff
try:
    from director.insert_admin_staff import insert_admin_staff_bp
    app.register_blueprint(insert_admin_staff_bp)
    print("✅ Insert Admin Staff registered")
except Exception as e:
    print(f"❌ Insert Admin Staff error: {e}")
    
# Import View Admin Staff
try:
    from director.view_admin_staff import view_admin_staff_bp
    app.register_blueprint(view_admin_staff_bp)
    print("✅ View Admin Staff registered")
except Exception as e:
    print(f"❌ View Admin Staff error: {e}")
    
# Import Insert Users
try:
    from director.insert_users import insert_users_bp
    app.register_blueprint(insert_users_bp)
    print("✅ Insert Users registered")
    print("  → URL: /director/insert_users")
except Exception as e:
    print(f"❌ Insert Users error: {e}") 
    
    # Import Manage Users
try:
    from director.manage_users import manage_users_bp
    app.register_blueprint(manage_users_bp)
    print("✅ Manage Users registered")
    print("  → URL: /director/manage_users")
except Exception as e:
    print(f"❌ Manage Users error: {e}")
    
    # Import View Users
try:
    from director.view_users import view_users_bp
    app.register_blueprint(view_users_bp)
    print("✅ View Users registered")
    print("  → URL: /director/view_users")
except Exception as e:
    print(f"❌ View Users error: {e}")
    
    # Import User Permissions
try:
    from director.user_permissions import user_permissions_bp
    app.register_blueprint(user_permissions_bp)
    print("✅ User Permissions registered")
    print("  → URL: /director/user_permissions")
except Exception as e:
    print(f"❌ User Permissions error: {e}")
    
# Import Activity Log
try:
    print("Attempting to import from director.activity_log...")
    from director.activity_log import activity_log_bp
    print(f"✅ Import successful! Blueprint: {activity_log_bp}")
    app.register_blueprint(activity_log_bp)
    print("✅ Activity Log registered")
    print("  → URL: /director/activity_log")
except Exception as e:
    print(f"❌ Activity Log error: {e}")
    import traceback
    traceback.print_exc()
# Import View Login Attempts
try:
    from director.view_login_attempts import view_login_attempts_bp
    app.register_blueprint(view_login_attempts_bp)
    print("✅ View Login Attempts registered")
    print("  → URL: /director/view_login_attempts")
except Exception as e:
    print(f"❌ View Login Attempts error: {e}")
    
    # Import Insert Academic Year
try:
    from director.insert_academic_year import insert_academic_year_bp
    app.register_blueprint(insert_academic_year_bp)
    print("✅ Insert Academic Year registered")
    print("  → URL: /director/insert_academic_year")
except Exception as e:
    print(f"❌ Insert Academic Year error: {e}")
    
try:
    # Import View Academic Year
    from director.view_academic_year import view_academic_year_bp
    app.register_blueprint(view_academic_year_bp)
    print("✅ View Academic Year registered")
    print("  → URL: /director/view_academic_year")
except Exception as e:
    print(f"❌ View Academic Year error: {e}")
    
    # Import Academic Year Converter
try:
    from director.academic_year_converter import academic_year_converter_bp
    app.register_blueprint(academic_year_converter_bp)
    print("✅ Academic Year Converter registered")
    print("  → URL: /director/academic_year_converter")
except Exception as e:
    print(f"❌ Academic Year Converter error: {e}")
    # Import View Graduated Students
try:
    from director.view_graduated_students import view_graduated_students_bp
    app.register_blueprint(view_graduated_students_bp)
    print("✅ View Graduated Students registered")
    print("  → URL: /director/view_graduated_students")
except Exception as e:
    print(f"❌ View Graduated Students error: {e}")
    # Import View Student Enrollment
try:
    from director.view_student_enrollment import view_student_enrollment_bp
    app.register_blueprint(view_student_enrollment_bp)
    print("✅ View Student Enrollment registered")
    print("  → URL: /director/view_student_enrollment")
except Exception as e:
    print(f"❌ View Student Enrollment error: {e}")
    
    # Import New Students
try:
    from director.new_students import new_students_bp
    app.register_blueprint(new_students_bp)
    print("✅ New Students registered")
    print("  → URL: /director/new_students")
except Exception as e:
    print(f"❌ New Students error: {e}")
    
# Print all registered routes after registration
print("\n📋 ALL REGISTERED ROUTES:")
for rule in app.url_map.iter_rules():
    print(f"  {rule.endpoint}: {rule.rule}")

# ============== DYNAMICALLY REGISTER ALL ROOM TEACHER DASHBOARDS ==============
def register_all_room_teacher_blueprints():
    """Dynamically find and register all room teacher dashboard blueprints"""
    room_teacher_base = os.path.join(os.path.dirname(__file__), 'room_teacher')
    registered_count = 0
    
    if os.path.exists(room_teacher_base):
        for folder in os.listdir(room_teacher_base):
            folder_path = os.path.join(room_teacher_base, folder)
            if os.path.isdir(folder_path) and folder.startswith('grade_'):
                # Look for the dashboard file
                dashboard_file = os.path.join(folder_path, f"{folder}_rt_dashboard.py")
                if os.path.exists(dashboard_file):
                    try:
                        # Dynamically import the module
                        spec = importlib.util.spec_from_file_location(f"{folder}_rt", dashboard_file)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Look for the blueprint variable
                        blueprint_name = f"{folder}_rt_bp"
                        if hasattr(module, blueprint_name):
                            bp = getattr(module, blueprint_name)
                            app.register_blueprint(bp)
                            registered_count += 1
                            print(f"✓ Registered: {folder}")
                            print(f"  → URL: /room_teacher/{folder}/{folder}_rt_dashboard")
                    except Exception as e:
                        print(f"✗ Error registering {folder}: {e}")
    
    return registered_count

# Register all room teacher dashboards
print("\n📚 Registering Room Teacher Dashboards:")
registered = register_all_room_teacher_blueprints()
print(f"\n✅ Total room teacher dashboards registered: {registered}\n")

# ============== LOGIN TEMPLATE ==============
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>School Management System - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            width: 400px;
        }
        h2 { text-align: center; color: #333; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }
        button:hover { opacity: 0.9; }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
        .info {
            background: #d4edda;
            color: #155724;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>🏫 School Management System</h2>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        {% if info %}
        <div class="info">{{ info }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Login</button>
        </form>
        <div style="margin-top: 20px; font-size: 12px; text-align: center; color: #666;">
            <p>Test Accounts (any password):</p>
            <p>Director: director001</p>
            <p>Grade 6A Teacher: TCH-002</p>
        </div>
    </div>
</body>
</html>
'''

# ============== DASHBOARD ROUTE MAPPING ==============
def get_dashboard_route(user_type):
    """Return the appropriate dashboard route based on user type"""
    
    # Directors
    if user_type == 'director':
        return '/director/director_dashboard'
    elif user_type == 'vice director':
        return '/vice_director/vice_director_dashboard'
    elif user_type == 'supervisor':
        return '/supervisor/supervisor_dashboard'
    elif user_type == 'KG director':
        return '/kg_director/kg_director_dashboard'
    
    # Room Teachers - Dynamic mapping for all grades
    if 'room teacher grade' in user_type.lower():
        # Extract grade and section (e.g., "room teacher grade 6th A" -> "6A")
        match = re.search(r'grade (\d+)(?:st|nd|rd|th)?\s*([A-E])', user_type, re.IGNORECASE)
        if match:
            grade = match.group(1)
            section = match.group(2)
            return f'/room_teacher/grade_{grade}{section}/grade_{grade}{section}_rt_dashboard'
    
    # Students and Parents
    elif 'student' in user_type.lower():
        return '/student/student_dashboard'
    elif user_type == 'parent' or user_type == '':
        return '/parent/parent_dashboard'
    
    # Default
    return '/dashboard'

# ============== ADDITIONAL DASHBOARD ROUTES ==============

# Vice Director Dashboard (placeholder until converted)
@app.route('/vice_director/vice_director_dashboard')
def vice_director_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'vice director':
        return redirect('/unauthorized')
    return '<h1>Vice Director Dashboard</h1><p>Under development</p><a href="/logout">Logout</a>'

# Supervisor Dashboard
@app.route('/supervisor/supervisor_dashboard')
def supervisor_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'supervisor':
        return redirect('/unauthorized')
    return '<h1>Supervisor Dashboard</h1><p>Under development</p><a href="/logout">Logout</a>'

# KG Director Dashboard
@app.route('/kg_director/kg_director_dashboard')
def kg_director_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'KG director':
        return redirect('/unauthorized')
    return '<h1>KG Director Dashboard</h1><p>Under development</p><a href="/logout">Logout</a>'

# Student Dashboard
@app.route('/student/student_dashboard')
def student_dashboard():
    if not session.get('logged_in') or 'student' not in session.get('user_type', '').lower():
        return redirect('/unauthorized')
    return '<h1>Student Dashboard</h1><p>Under development</p><a href="/logout">Logout</a>'

# Parent Dashboard
@app.route('/parent/parent_dashboard')
def parent_dashboard():
    if not session.get('logged_in'):
        return redirect('/unauthorized')
    return '<h1>Parent Dashboard</h1><p>Under development</p><a href="/logout">Logout</a>'
    
    # Import View Admin Staff
try:
    from director.view_admin_staff import view_admin_staff_bp
    app.register_blueprint(view_admin_staff_bp)
    print("✅ View Admin Staff registered")
    print("  → URL: /director/view_admin_staff")
except Exception as e:
    print(f"❌ View Admin Staff error: {e}")

# ============== LOGIN ROUTE ==============
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template_string(LOGIN_TEMPLATE, error="Please enter both username and password.")
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT user_id, username, user_type, reference_id, account_status 
                FROM users 
                WHERE username = %s LIMIT 1
            """, (username,))
            user = cursor.fetchone()
            
            if user and user['account_status'] == 'active':
                # For testing - accept any password
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['user_type'] = user['user_type']
                session['reference_id'] = user['reference_id']
                session['logged_in'] = True
                
                # ========== LOG THE LOGIN ACTIVITY ==========
                # This records the login in the activity_log table
                log_activity(
                    user_id=user['user_id'],
                    username=user['username'],
                    user_type=user['user_type'],
                    action='LOGIN',
                    details='User logged in successfully',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')
                )
                # ========== END OF LOGIN LOGGING ==========
                
                # Update last login
                cursor.execute("UPDATE users SET last_login = NOW() WHERE user_id = %s", (user['user_id'],))
                conn.commit()
                
                cursor.close()
                conn.close()
                
                # Redirect to appropriate dashboard
                dashboard_route = get_dashboard_route(user['user_type'])
                print(f"\n✅ Login successful: {username} ({user['user_type']})")
                print(f"   Redirecting to: {dashboard_route}\n")
                return redirect(dashboard_route)
            else:
                # ========== LOG FAILED LOGIN ATTEMPT ==========
                log_activity(
                    user_id=None,
                    username=username,
                    user_type='unknown',
                    action='LOGIN_FAILED',
                    details=f'Failed login attempt for username: {username}',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')
                )
                # ========== END OF FAILED LOGIN LOGGING ==========
                
                cursor.close()
                conn.close()
                return render_template_string(LOGIN_TEMPLATE, error="Invalid username or inactive account.")
                
        except Exception as e:
            cursor.close()
            conn.close()
            print(f"Database error: {e}")
            return render_template_string(LOGIN_TEMPLATE, error=f"Database error. Please try again.")
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/')
def index():
    return redirect('/login')

@app.route('/logout')
def logout():
    # Log the logout activity
    if session.get('logged_in'):
        log_activity(
            user_id=session.get('user_id'),
            username=session.get('username'),
            user_type=session.get('user_type'),
            action='LOGOUT',
            details='User logged out',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
    session.clear()
    return redirect('/login')

@app.route('/unauthorized')
def unauthorized():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unauthorized Access</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                max-width: 500px;
                margin: 0 auto;
            }
            h1 { color: #e74c3c; }
            a { color: #667eea; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚫 Unauthorized Access</h1>
            <p>You don't have permission to access this page.</p>
            <p><a href="/login">Return to Login</a></p>
        </div>
    </body>
    </html>
    '''

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/login')
    return f'''
    <h1>Welcome {session.get("username")}</h1>
    <p>User Type: {session.get("user_type")}</p>
    <p>This is a generic dashboard. Please configure a specific dashboard for this user type.</p>
    <a href="/logout">Logout</a>
    '''

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏫 SCHOOL MANAGEMENT SYSTEM - PYTHON VERSION")
    print("="*60)
    print(f"Server: http://127.0.0.1:5000")
    print(f"Login: http://127.0.0.1:5000/login")
    print("\n" + "="*60)
    print("REGISTERED DASHBOARDS:")
    print("="*60)
    
    # List all registered dashboard routes
    dashboard_routes = []
    for rule in app.url_map.iter_rules():
        rule_str = str(rule)
        if 'dashboard' in rule_str or 'director' in rule_str or 'room_teacher' in rule_str:
            dashboard_routes.append(rule_str)
    
    for route in sorted(dashboard_routes):
        print(f"  {route}")
    
    print("\n" + "="*60)
    print("🔑 TEST LOGINS (any password):")
    print("="*60)
    print("  Director:           director001")
    print("  Grade 6A Teacher:   TCH-002")
    print("  Grade 6B Teacher:   TCH-003 (if exists)")
    print("="*60 + "\n")
   
    app.run(debug=True, host='127.0.0.1', port=5000)