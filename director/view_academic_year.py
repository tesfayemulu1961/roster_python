from flask import Blueprint, session, redirect, request, render_template_string, jsonify
from functools import wraps
import mysql.connector
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
view_academic_year_bp = Blueprint('view_academic_year', __name__, url_prefix='/director')

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
VIEW_ACADEMIC_YEAR_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Academic Years</title>
    <style>
        body { 
            background-color: #f8f9fa; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        }
        .container { 
            max-width: 1200px; 
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
        .card-header .btn-group {
            display: flex;
            gap: 10px;
        }
        .table-responsive { 
            overflow-x: auto; 
        }
        .table { 
            width: 100%; 
            border-collapse: collapse; 
        }
        .table th, .table td { 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #ddd; 
        }
        .table th { 
            background-color: #f8f9fa; 
            font-weight: 600; 
            white-space: nowrap;
        }
        .table tr:hover { 
            background-color: #f5f5f5; 
        }
        .badge { 
            padding: 4px 8px; 
            border-radius: 20px; 
            font-size: 12px; 
            font-weight: 600; 
            display: inline-block;
        }
        .badge-active { 
            background-color: #28a745; 
            color: white; 
        }
        .badge-inactive { 
            background-color: #6c757d; 
            color: white; 
        }
        .current-year { 
            background-color: #e8f4fd; 
        }
        .btn-sm { 
            padding: 4px 8px; 
            font-size: 12px; 
            border-radius: 4px; 
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .btn-outline-primary { 
            border: 1px solid #007bff; 
            color: #007bff; 
            background: transparent;
        }
        .btn-outline-primary:hover { 
            background-color: #007bff; 
            color: white; 
        }
        .btn-outline-danger { 
            border: 1px solid #dc3545; 
            color: #dc3545; 
            background: transparent;
        }
        .btn-outline-danger:hover { 
            background-color: #dc3545; 
            color: white; 
        }
        .btn-success { 
            background-color: #28a745; 
            color: white; 
            border: none;
        }
        .btn-success:hover { 
            background-color: #218838; 
        }
        .btn-primary { 
            background-color: #007bff; 
            color: white; 
            border: none;
        }
        .btn-primary:hover { 
            background-color: #0069d9; 
        }
        .btn-outline-secondary { 
            border: 1px solid #6c757d; 
            color: #6c757d; 
            background: transparent;
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
        .alert-danger { 
            background-color: #f8d7da; 
            border: 1px solid #f5c6cb; 
            color: #721c24; 
        }
        .alert-info { 
            background-color: #d1ecf1; 
            border: 1px solid #bee5eb; 
            color: #0c5460; 
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
        .mt-3 { 
            margin-top: 1rem; 
        }
        .d-flex { 
            display: flex; 
        }
        .justify-content-between { 
            justify-content: space-between; 
        }
        .align-items-center { 
            align-items: center; 
        }
        .input-group { 
            display: flex; 
            gap: 5px; 
        }
        .form-control { 
            padding: 8px 12px; 
            border: 1px solid #ced4da; 
            border-radius: 4px; 
            font-size: 14px; 
            flex: 1;
        }
        .search-box { 
            max-width: 300px; 
        }
        .dropdown { 
            position: relative; 
            display: inline-block; 
        }
        .dropdown-toggle { 
            cursor: pointer; 
        }
        .dropdown-menu { 
            position: absolute; 
            right: 0; 
            background: white; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
            min-width: 150px; 
            display: none; 
            z-index: 1000;
        }
        .dropdown-menu.show { 
            display: block; 
        }
        .dropdown-item { 
            display: block; 
            padding: 8px 16px; 
            text-decoration: none; 
            color: #333; 
        }
        .dropdown-item:hover { 
            background-color: #f8f9fa; 
        }
        .dropdown-divider { 
            height: 1px; 
            background-color: #ddd; 
            margin: 8px 0; 
        }
        .text-end { 
            text-align: right; 
        }
        .me-2 { 
            margin-right: 0.5rem; 
        }
        .ms-2 { 
            margin-left: 0.5rem; 
        }
        .sort-link {
            text-decoration: none;
            color: #333;
            cursor: pointer;
        }
        .sort-link:hover {
            text-decoration: underline;
        }
        @media (max-width: 768px) {
            .container {
                margin: 15px;
            }
            .d-flex.justify-content-between {
                flex-direction: column;
                gap: 10px;
            }
            .search-box {
                max-width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center my-4">Academic Years</h1>
        
        {% if message %}
            <div class="alert alert-danger">{{ message|safe }}</div>
        {% endif %}
        
        <div class="card shadow mb-4">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h3 class="mb-0">Academic Year List</h3>
                <div class="btn-group">
                    <a href="/director/insert_academic_year" class="btn-sm btn-success" style="padding: 6px 12px; text-decoration: none;">
                        ➕ Add New
                    </a>
                    <a href="/director/academic_year_converter" class="btn-sm btn-primary ms-2" style="padding: 6px 12px; text-decoration: none;">
                        🔄 Convert Year
                    </a>
                </div>
            </div>
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div class="search-box">
                        <form method="GET" class="input-group">
                            <input type="text" class="form-control" name="search" 
                                   placeholder="Search..." value="{{ search_query }}">
                            <button type="submit" class="btn-sm btn-outline-secondary">🔍</button>
                            {% if search_query %}
                                <a href="/director/view_academic_year" class="btn-sm btn-outline-danger">✗</a>
                            {% endif %}
                        </form>
                    </div>
                    <div class="text-end">
                        <div class="dropdown">
                            <button class="btn-sm btn-outline-secondary dropdown-toggle" onclick="toggleDropdown()">
                                🎛️ Filter
                            </button>
                            <div id="filterDropdown" class="dropdown-menu">
                                <a class="dropdown-item" href="?status=active">Active Only</a>
                                <a class="dropdown-item" href="?status=inactive">Inactive Only</a>
                                <div class="dropdown-divider"></div>
                                <a class="dropdown-item" href="/director/view_academic_year">Show All</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th><a href="?sort=year&order={{ 'ASC' if sort == 'year' and order == 'DESC' else 'DESC' }}" class="sort-link">Academic Year {% if sort == 'year' %}{{ '↑' if order == 'ASC' else '↓' }}{% endif %}</a></th>
                                <th><a href="?sort=start_date&order={{ 'ASC' if sort == 'start_date' and order == 'DESC' else 'DESC' }}" class="sort-link">Start Date {% if sort == 'start_date' %}{{ '↑' if order == 'ASC' else '↓' }}{% endif %}</a></th>
                                <th><a href="?sort=end_date&order={{ 'ASC' if sort == 'end_date' and order == 'DESC' else 'DESC' }}" class="sort-link">End Date {% if sort == 'end_date' %}{{ '↑' if order == 'ASC' else '↓' }}{% endif %}</a></th>
                                <th><a href="?sort=is_active&order={{ 'ASC' if sort == 'is_active' and order == 'DESC' else 'DESC' }}" class="sort-link">Status {% if sort == 'is_active' %}{{ '↑' if order == 'ASC' else '↓' }}{% endif %}</a></th>
                                <th>Duration</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% if not academic_years %}
                                <tr>
                                    <td colspan="6" class="text-center">No academic years found</td>
                                </tr>
                            {% else %}
                                {% for year in academic_years %}
                                    <tr class="{{ 'current-year' if year.is_active == 1 else '' }}">
                                        <td>{{ year.year }}</td>
                                        <td>{{ year.start_date_formatted }}</td>
                                        <td>{{ year.end_date_formatted }}</td>
                                        <td>
                                            <span class="badge {{ 'badge-active' if year.is_active == 1 else 'badge-inactive' }}">
                                                {{ 'Active' if year.is_active == 1 else 'Inactive' }}
                                            </span>
                                        </td>
                                        <td>{{ year.duration }}</td>
                                        <td class="action-btns">
                                            <a href="/director/edit_academic_year?id={{ year.id }}" class="btn-sm btn-outline-primary" style="text-decoration: none;">✏️</a>
                                            <a href="/director/delete_academic_year?id={{ year.id }}" class="btn-sm btn-outline-danger ms-2" style="text-decoration: none;" onclick="return confirm('Are you sure you want to delete this academic year?')">🗑️</a>
                                        </td>
                                    </tr>
                                {% endfor %}
                            {% endif %}
                        </tbody>
                    </table>
                </div>
                
                {% if current_year %}
                    <div class="alert alert-info mt-3">
                        <strong>Current Academic Year:</strong> {{ current_year.year }}
                        ({{ current_year.start_date_formatted }} to {{ current_year.end_date_formatted }})
                    </div>
                {% endif %}
            </div>
        </div>
    </div>

    <script>
        function toggleDropdown() {
            const dropdown = document.getElementById('filterDropdown');
            dropdown.classList.toggle('show');
        }
        
        // Close dropdown when clicking outside
        window.onclick = function(event) {
            if (!event.target.matches('.dropdown-toggle')) {
                const dropdowns = document.getElementsByClassName('dropdown-menu');
                for (let i = 0; i < dropdowns.length; i++) {
                    if (dropdowns[i].classList.contains('show')) {
                        dropdowns[i].classList.remove('show');
                    }
                }
            }
        }
        
        // Highlight current year row on hover
        const currentYearRows = document.querySelectorAll('.current-year');
        currentYearRows.forEach(row => {
            row.addEventListener('mouseover', () => {
                row.style.backgroundColor = '#d1e7ff';
            });
            row.addEventListener('mouseout', () => {
                row.style.backgroundColor = '#e8f4fd';
            });
        });
    </script>
</body>
</html>
'''

@view_academic_year_bp.route('/view_academic_year')
@login_required
def view_academic_year():
    """Display all academic years with sorting and filtering"""
    try:
        # Only directors should access this
        if session.get('user_type') != 'director':
            return redirect('/unauthorized')
        
        # Get sorting parameters
        sort = request.args.get('sort', 'year')
        order = request.args.get('order', 'DESC')
        search_query = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        
        # Validate sort parameters
        valid_sorts = ['id', 'year', 'start_date', 'end_date', 'is_active']
        valid_orders = ['ASC', 'DESC']
        
        if sort not in valid_sorts:
            sort = 'year'
        if order not in valid_orders:
            order = 'DESC'
        
        # Build query
        query = "SELECT * FROM academic_year WHERE 1=1"
        params = []
        
        if search_query:
            query += " AND (year LIKE %s OR start_date LIKE %s OR end_date LIKE %s)"
            search_param = f'%{search_query}%'
            params.extend([search_param, search_param, search_param])
        
        if status_filter == 'active':
            query += " AND is_active = 1"
        elif status_filter == 'inactive':
            query += " AND is_active = 0"
        
        query += f" ORDER BY {sort} {order}"
        
        # Execute query
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(query, params)
        academic_years = cursor.fetchall()
        
        # Get current active academic year
        cursor.execute("SELECT * FROM academic_year WHERE is_active = 1 LIMIT 1")
        current_year_data = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Format dates and calculate duration
        for year in academic_years:
            if year['start_date']:
                start_date = year['start_date']
                year['start_date_formatted'] = start_date.strftime('%b %d, %Y')
                
                if year['end_date']:
                    end_date = year['end_date']
                    year['end_date_formatted'] = end_date.strftime('%b %d, %Y')
                    
                    # Calculate duration
                    delta = end_date - start_date
                    months = delta.days // 30
                    days = delta.days % 30
                    year['duration'] = f'{months} months {days} days'
            else:
                year['start_date_formatted'] = 'N/A'
                year['end_date_formatted'] = 'N/A'
                year['duration'] = 'N/A'
        
        # Format current year dates
        current_year = None
        if current_year_data:
            current_year = current_year_data.copy()
            if current_year.get('start_date'):
                current_year['start_date_formatted'] = current_year['start_date'].strftime('%b %d, %Y')
            if current_year.get('end_date'):
                current_year['end_date_formatted'] = current_year['end_date'].strftime('%b %d, %Y')
        
        return render_template_string(
            VIEW_ACADEMIC_YEAR_TEMPLATE,
            academic_years=academic_years,
            current_year=current_year,
            sort=sort,
            order=order,
            search_query=search_query,
            message=''
        )
        
    except mysql.connector.Error as e:
        return render_template_string(
            VIEW_ACADEMIC_YEAR_TEMPLATE,
            academic_years=[],
            current_year=None,
            sort='year',
            order='DESC',
            search_query='',
            message=f'Database error: {str(e)}'
        )


# API endpoint for JSON data (optional)
@view_academic_year_bp.route('/api/academic_years')
@login_required
def api_academic_years():
    """Return academic years as JSON"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM academic_year ORDER BY year DESC")
        years = cursor.fetchall()
        
        # Format dates
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