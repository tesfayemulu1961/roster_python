from flask import Blueprint, session, redirect, request, render_template_string, flash
from functools import wraps
import mysql.connector
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
insert_academic_year_bp = Blueprint('insert_academic_year', __name__, url_prefix='/director')

# Database configuration
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
        return f(*args, **kwargs)
    return decorated_function

# HTML Template
INSERT_ACADEMIC_YEAR_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add New Academic Year</title>
    <style>
        body { 
            background-color: #f8f9fa; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        }
        .container { 
            max-width: 700px; 
            margin: 30px auto 50px auto; 
        }
        .card { 
            border-radius: 10px; 
            overflow: hidden; 
            border: none; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        }
        .card-header { 
            padding: 15px 20px; 
            font-weight: 600; 
            background-color: #2c3e50; 
            color: white; 
        }
        .card-header h3 {
            margin: 0;
            font-size: 1.25rem;
        }
        .form-label { 
            font-weight: 500; 
            margin-bottom: 5px;
            display: block;
        }
        .required-field::after { 
            content: " *"; 
            color: red; 
        }
        .form-text {
            font-size: 12px;
            color: #6c757d;
            margin-top: 5px;
        }
        .form-control {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 14px;
        }
        .form-control:focus {
            border-color: #80bdff;
            outline: 0;
            box-shadow: 0 0 0 0.2rem rgba(0,123,255,0.25);
        }
        .btn {
            padding: 8px 24px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            border: none;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        .btn-primary {
            background-color: #007bff;
            color: white;
        }
        .btn-primary:hover {
            background-color: #0069d9;
        }
        .btn-outline-secondary {
            background-color: transparent;
            border: 1px solid #6c757d;
            color: #6c757d;
        }
        .btn-outline-secondary:hover {
            background-color: #6c757d;
            color: white;
        }
        .alert {
            padding: 12px 20px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .alert-success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .alert-danger {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .alert-danger ul {
            margin: 0;
            padding-left: 20px;
        }
        .text-center {
            text-align: center;
        }
        .my-4 {
            margin-top: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .mb-3 {
            margin-bottom: 1rem;
        }
        .mb-0 {
            margin-bottom: 0;
        }
        .d-grid {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        .row {
            display: flex;
            gap: 15px;
            margin-bottom: 1rem;
        }
        .col-md-6 {
            flex: 1;
        }
        @media (max-width: 768px) {
            .row {
                flex-direction: column;
            }
            .container {
                margin: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center my-4">Add New Academic Year</h1>
        
        {% if message %}
            <div class="alert {{ 'alert-success' if 'success' in message else 'alert-danger' }}">
                {{ message|safe }}
            </div>
        {% endif %}
        
        <div class="card shadow">
            <div class="card-header">
                <h3 class="mb-0">Academic Year Information</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="year" class="form-label required-field">Academic Year</label>
                        <input type="text" class="form-control" id="year" name="year" 
                               value="{{ year }}" 
                               placeholder="e.g., 2024" required>
                        <div class="form-text">Enter the academic year (4 digits)</div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <label for="start_date" class="form-label required-field">Start Date</label>
                            <input type="date" class="form-control" id="start_date" name="start_date" 
                                   value="{{ start_date }}" required>
                        </div>
                        <div class="col-md-6">
                            <label for="end_date" class="form-label required-field">End Date</label>
                            <input type="date" class="form-control" id="end_date" name="end_date" 
                                   value="{{ end_date }}" required>
                        </div>
                    </div>
                    
                    <div class="d-grid">
                        <button type="submit" name="submit" class="btn btn-primary">Add Academic Year</button>
                        <a href="/director/academic_year_converter" class="btn btn-outline-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        // Client-side validation for date ranges
        document.addEventListener('DOMContentLoaded', function() {
            const startDate = document.getElementById('start_date');
            const endDate = document.getElementById('end_date');
            
            function validateDates() {
                if (startDate.value && endDate.value) {
                    if (new Date(endDate.value) <= new Date(startDate.value)) {
                        endDate.setCustomValidity('End date must be after start date');
                    } else {
                        endDate.setCustomValidity('');
                    }
                }
            }
            
            startDate.addEventListener('change', validateDates);
            endDate.addEventListener('change', validateDates);
            
            // Year input validation - only allow 4 digits
            const yearInput = document.getElementById('year');
            yearInput.addEventListener('input', function() {
                this.value = this.value.replace(/[^0-9]/g, '').slice(0, 4);
            });
        });
    </script>
</body>
</html>
'''

@insert_academic_year_bp.route('/insert_academic_year', methods=['GET', 'POST'])
@login_required
def insert_academic_year():
    """Add new academic year to the system"""
    
    # Initialize variables
    message = ''
    year = ''
    start_date = ''
    end_date = ''
    errors = []
    
    # Only directors should access this
    if session.get('user_type') != 'director':
        return redirect('/unauthorized')
    
    # Process form submission
    if request.method == 'POST' and request.form.get('submit'):
        year = request.form.get('year', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        
        # Validate inputs
        if not year:
            errors.append("Academic year is required")
        elif not year.isdigit() or len(year) != 4:
            errors.append("Academic year must be a 4-digit number")
        
        if not start_date:
            errors.append("Start date is required")
        
        if not end_date:
            errors.append("End date is required")
        elif start_date and end_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                if end_date_obj <= start_date_obj:
                    errors.append("End date must be after start date")
            except ValueError:
                errors.append("Invalid date format")
        
        # If no errors, insert into database
        if not errors:
            try:
                conn = get_db()
                cursor = conn.cursor()
                
                # Check if year already exists
                cursor.execute("SELECT id FROM academic_year WHERE year = %s", (year,))
                existing = cursor.fetchone()
                
                if existing:
                    errors.append("Academic year already exists")
                else:
                    # Insert new academic year
                    cursor.execute("""
                        INSERT INTO academic_year (year, start_date, end_date) 
                        VALUES (%s, %s, %s)
                    """, (year, start_date, end_date))
                    
                    conn.commit()
                    message = '<div class="alert alert-success">Academic year added successfully!</div>'
                    
                    # Clear form fields
                    year = ''
                    start_date = ''
                    end_date = ''
                
                cursor.close()
                conn.close()
                
            except mysql.connector.Error as e:
                message = f'<div class="alert alert-danger">Database error: {str(e)}</div>'
        
        # Display errors if any
        if errors:
            error_html = '<ul>'
            for error in errors:
                error_html += f'<li>{error}</li>'
            error_html += '</ul>'
            message = f'<div class="alert alert-danger">{error_html}</div>'
    
    return render_template_string(
        INSERT_ACADEMIC_YEAR_TEMPLATE,
        message=message,
        year=year,
        start_date=start_date,
        end_date=end_date
    )


# API endpoint for AJAX calls (optional)
@insert_academic_year_bp.route('/api/academic_years', methods=['GET'])
@login_required
def get_academic_years():
    """Return list of academic years as JSON"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, year, start_date, end_date, 
                   CASE 
                       WHEN YEAR(CURDATE()) = year THEN 'Current'
                       WHEN YEAR(CURDATE()) < year THEN 'Future'
                       ELSE 'Past'
                   END as status
            FROM academic_year 
            ORDER BY year DESC
        """)
        
        years = cursor.fetchall()
        
        # Convert dates to string for JSON
        for year in years:
            if year['start_date']:
                year['start_date'] = year['start_date'].strftime('%Y-%m-%d')
            if year['end_date']:
                year['end_date'] = year['end_date'].strftime('%Y-%m-%d')
        
        cursor.close()
        conn.close()
        
        return {'success': True, 'data': years}
        
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500