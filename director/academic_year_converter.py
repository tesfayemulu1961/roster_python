from flask import Blueprint, session, redirect, request, render_template_string, flash
from functools import wraps
import mysql.connector
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
academic_year_converter_bp = Blueprint('academic_year_converter', __name__, url_prefix='/director')

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
ACADEMIC_YEAR_CONVERTER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Academic Year Converter</title>
    <style>
        body {
            background-color: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .container {
            max-width: 900px;
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
        }
        .card-header.bg-primary {
            background-color: #0d6efd;
            color: white;
        }
        .card-header.bg-info {
            background-color: #0dcaf0;
            color: white;
        }
        .card-title {
            margin: 0;
            font-size: 1.25rem;
        }
        .form-select, .form-control {
            padding: 10px 15px;
            border-radius: 8px;
            border: 1px solid #ced4da;
            width: 100%;
            font-size: 14px;
        }
        .form-label {
            font-weight: 500;
            margin-bottom: 8px;
            display: block;
        }
        .btn-primary {
            background-color: #0d6efd;
            border: none;
            padding: 10px 25px;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            color: white;
            font-size: 16px;
        }
        .btn-primary:hover {
            background-color: #0b5ed7;
        }
        .btn-back {
            display: inline-block;
            padding: 8px 16px;
            background-color: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .btn-back:hover {
            background-color: #5a6268;
        }
        .alert {
            border-radius: 8px;
            padding: 15px;
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
        .alert-warning {
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
            color: #856404;
        }
        .current-year-display {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .current-year-display h2 {
            font-size: 2.5rem;
            color: #0d6efd;
            margin-bottom: 10px;
        }
        .current-year-display p {
            font-size: 1.1rem;
            color: #495057;
            margin: 10px 0;
        }
        .badge {
            font-size: 0.9rem;
            padding: 5px 10px;
            border-radius: 20px;
            display: inline-block;
        }
        .badge-success {
            background-color: #28a745;
            color: white;
        }
        .text-muted {
            font-size: 0.85rem;
            margin-left: 10px;
            color: #6c757d;
        }
        .row {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .col-md-6 {
            flex: 1;
        }
        .text-center {
            text-align: center;
        }
        .mt-4 {
            margin-top: 1.5rem;
        }
        .mb-0 {
            margin-bottom: 0;
        }
        .mb-3 {
            margin-bottom: 1rem;
        }
        .px-5 {
            padding-left: 3rem;
            padding-right: 3rem;
        }
        i {
            margin-right: 5px;
        }
        @media (max-width: 768px) {
            .container {
                margin: 15px;
            }
            .row {
                flex-direction: column;
                gap: 15px;
            }
            .current-year-display h2 {
                font-size: 1.8rem;
            }
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <a href="/director/director_dashboard" class="btn-back">
            <i class="fas fa-backward"></i> Back
        </a>
        
        <h2 style="margin-bottom: 20px;"><i class="fas fa-exchange-alt"></i> Academic Year Converter</h2>
        
        {% if message %}
            <div class="alert {{ 'alert-success' if 'success' in message else 'alert-warning' if 'warning' in message else 'alert-danger' }}">
                {{ message|safe }}
            </div>
        {% endif %}
        
        <div class="card shadow">
            <div class="card-header bg-primary">
                <h3 class="card-title mb-0">Convert Academic Year</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="row">
                        <div class="col-md-6">
                            <label for="from_year" class="form-label">From Academic Year</label>
                            <select class="form-select" id="from_year" name="from_year" required>
                                <option value="">Select Academic Year</option>
                                {% for year in academic_years %}
                                    <option value="{{ year.id }}" {% if year.is_active == 1 %}selected{% endif %}>
                                        {{ year.year }} 
                                        ({{ year.start_date_formatted }} - {{ year.end_date_formatted }})
                                        {% if year.is_active == 1 %}(Current){% endif %}
                                    </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label for="to_year" class="form-label">To Academic Year</label>
                            <select class="form-select" id="to_year" name="to_year" required>
                                <option value="">Select Academic Year</option>
                                {% for year in academic_years %}
                                    {% if year.is_active != 1 %}
                                        <option value="{{ year.id }}">
                                            {{ year.year }} 
                                            ({{ year.start_date_formatted }} - {{ year.end_date_formatted }})
                                        </option>
                                    {% endif %}
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    
                    <div class="text-center">
                        <button type="submit" name="convert" class="btn-primary px-5">Convert Academic Year</button>
                    </div>
                </form>
            </div>
        </div>
        
        <div class="card shadow mt-4">
            <div class="card-header bg-info">
                <h3 class="card-title mb-0">Current Academic Year</h3>
            </div>
            <div class="card-body">
                {% if current_year %}
                    <div class="current-year-display">
                        <h2>{{ current_year.year }}</h2>
                        <p>
                            {{ current_year.start_date_formatted }} to {{ current_year.end_date_formatted }}
                        </p>
                        <p>
                            <span class="badge badge-success">Active</span>
                            {% if current_year.updated_at %}
                                <small class="text-muted">Last updated: {{ current_year.updated_at_formatted }}</small>
                            {% endif %}
                        </p>
                    </div>
                {% else %}
                    <div class="alert alert-warning">No active academic year found.</div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
'''

def get_academic_years(conn):
    """Get all academic years"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM academic_year ORDER BY year DESC")
    years = cursor.fetchall()
    cursor.close()
    return years

def get_current_academic_year(conn):
    """Get current active academic year"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM academic_year WHERE is_active = 1 LIMIT 1")
    current = cursor.fetchone()
    cursor.close()
    return current

def convert_academic_year(conn, from_year_id, to_year_id):
    """Convert from one academic year to another"""
    try:
        cursor = conn.cursor()
        
        # Deactivate all years
        cursor.execute("UPDATE academic_year SET is_active = 0")
        
        # Activate the selected year
        cursor.execute("UPDATE academic_year SET is_active = 1 WHERE id = %s", (to_year_id,))
        
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error converting academic year: {e}")
        return False

@academic_year_converter_bp.route('/academic_year_converter', methods=['GET', 'POST'])
@login_required
def academic_year_converter():
    """Convert academic year - change which year is active"""
    
    # Only directors should access this
    if session.get('user_type') != 'director':
        return redirect('/unauthorized')
    
    message = ''
    
    try:
        conn = get_db()
        
        # Process form submission
        if request.method == 'POST' and request.form.get('convert'):
            from_year_id = request.form.get('from_year', '').strip()
            to_year_id = request.form.get('to_year', '').strip()
            
            if not from_year_id or not to_year_id:
                message = '<div class="alert alert-warning">Please select both academic years.</div>'
            elif from_year_id == to_year_id:
                message = '<div class="alert alert-warning">Cannot convert to the same academic year.</div>'
            else:
                success = convert_academic_year(conn, from_year_id, to_year_id)
                if success:
                    message = '<div class="alert alert-success">Academic year converted successfully!</div>'
                else:
                    message = '<div class="alert alert-danger">Error converting academic year.</div>'
        
        # Get data
        academic_years = get_academic_years(conn)
        current_year = get_current_academic_year(conn)
        
        conn.close()
        
        # Format dates for display
        for year in academic_years:
            if year['start_date']:
                year['start_date_formatted'] = year['start_date'].strftime('%b %d, %Y')
            else:
                year['start_date_formatted'] = 'N/A'
            
            if year['end_date']:
                year['end_date_formatted'] = year['end_date'].strftime('%b %d, %Y')
            else:
                year['end_date_formatted'] = 'N/A'
        
        if current_year:
            if current_year['start_date']:
                current_year['start_date_formatted'] = current_year['start_date'].strftime('%B %d, %Y')
            if current_year['end_date']:
                current_year['end_date_formatted'] = current_year['end_date'].strftime('%B %d, %Y')
            if current_year.get('updated_at'):
                current_year['updated_at_formatted'] = current_year['updated_at'].strftime('%B %d, %Y %H:%M')
        
        return render_template_string(
            ACADEMIC_YEAR_CONVERTER_TEMPLATE,
            academic_years=academic_years,
            current_year=current_year,
            message=message
        )
        
    except mysql.connector.Error as e:
        return render_template_string(
            ACADEMIC_YEAR_CONVERTER_TEMPLATE,
            academic_years=[],
            current_year=None,
            message=f'<div class="alert alert-danger">Database error: {str(e)}</div>'
        )


# API endpoint for JSON (optional)
@academic_year_converter_bp.route('/api/current_academic_year')
@login_required
def api_current_academic_year():
    """Return current academic year as JSON"""
    try:
        conn = get_db()
        current_year = get_current_academic_year(conn)
        conn.close()
        
        if current_year:
            return {
                'success': True,
                'data': {
                    'id': current_year['id'],
                    'year': current_year['year'],
                    'start_date': current_year['start_date'].strftime('%Y-%m-%d') if current_year['start_date'] else None,
                    'end_date': current_year['end_date'].strftime('%Y-%m-%d') if current_year['end_date'] else None
                }
            }
        else:
            return {'success': True, 'data': None}
            
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500