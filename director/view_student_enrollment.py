from flask import Blueprint, session, redirect, request, render_template_string, jsonify, make_response
from functools import wraps
import mysql.connector
import sys
import os
from datetime import datetime
import csv
from io import StringIO
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
view_student_enrollment_bp = Blueprint('view_student_enrollment', __name__, url_prefix='/director')

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

def parse_stud_id(studid):
    """Parse student ID to extract grade, section, and number"""
    if not studid or studid == 'N/A':
        return {'grade': 'N/A', 'section': 'N/A', 'number': 'N/A'}
    parts = studid.split('/')
    return {
        'grade': parts[2] if len(parts) > 2 else 'N/A',
        'section': parts[3] if len(parts) > 3 else 'N/A',
        'number': parts[4] if len(parts) > 4 else 'N/A'
    }

def get_table_columns(pdo, table_name):
    """Get column names of a table"""
    cursor = pdo.cursor(dictionary=True)
    cursor.execute(f"SHOW COLUMNS FROM {table_name}")
    columns = cursor.fetchall()
    cursor.close()
    return [col['Field'] for col in columns]

def is_studid_unique_for_year3(pdo, studid, exclude_id=None):
    """Check if student ID is unique for academic year 3"""
    query = "SELECT COUNT(*) as count FROM enrollment WHERE studid = %s AND academic_year_id = 3"
    params = [studid]
    
    if exclude_id:
        query += " AND id != %s"
        params.append(exclude_id)
    
    cursor = pdo.cursor(dictionary=True)
    cursor.execute(query, params)
    result = cursor.fetchone()
    cursor.close()
    
    return result['count'] == 0

@view_student_enrollment_bp.route('/view_student_enrollment', methods=['GET', 'POST'])
@login_required
def view_student_enrollment():
    """Display student enrollment data with inline editing"""
    
    # Only directors should access this
    if session.get('user_type') != 'director':
        return redirect('/unauthorized')
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Handle POST request for inline editing
        if request.method == 'POST' and request.form.get('update_enrollment'):
            try:
                enrollment_id = request.form.get('enrollment_id')
                field = request.form.get('field')
                value = request.form.get('value')
                
                # Get primary key field
                cursor.execute("SHOW COLUMNS FROM enrollment")
                columns = cursor.fetchall()
                primary_key_field = 'id'
                for col in columns:
                    if col['Key'] == 'PRI':
                        primary_key_field = col['Field']
                        break
                
                # Special case for section_name
                if field == 'section_name':
                    # Get section_id for this enrollment
                    cursor.execute(f"SELECT section_id FROM enrollment WHERE {primary_key_field} = %s", (enrollment_id,))
                    section_result = cursor.fetchone()
                    
                    if section_result and section_result.get('section_id'):
                        # Update section name
                        cursor.execute("UPDATE section SET sec_name = %s WHERE id = %s", (value, section_result['section_id']))
                        conn.commit()
                    else:
                        raise Exception("Cannot update section name: No section assigned to this enrollment")
                
                # Student ID uniqueness validation for academic_year_id = 3
                elif field == 'studid' and value:
                    # Get academic year for this enrollment
                    cursor.execute(f"SELECT academic_year_id FROM enrollment WHERE {primary_key_field} = %s", (enrollment_id,))
                    academic_info = cursor.fetchone()
                    
                    if academic_info and academic_info['academic_year_id'] == 3:
                        # Check for duplicates
                        cursor.execute(f"SELECT COUNT(*) as count FROM enrollment WHERE studid = %s AND academic_year_id = 3 AND {primary_key_field} != %s", (value, enrollment_id))
                        duplicate_result = cursor.fetchone()
                        
                        if duplicate_result and duplicate_result['count'] > 0:
                            # Get academic year name
                            cursor.execute("SELECT year FROM academic_year WHERE id = 3")
                            year_info = cursor.fetchone()
                            year_name = year_info['year'] if year_info else '3'
                            raise Exception(f"Student ID '{value}' already exists in academic year {year_name}. Please use a unique ID.")
                    
                    # Proceed with update
                    cursor.execute(f"UPDATE enrollment SET {field} = %s WHERE {primary_key_field} = %s", (value, enrollment_id))
                    conn.commit()
                
                # For all other fields
                else:
                    cursor.execute(f"UPDATE enrollment SET {field} = %s WHERE {primary_key_field} = %s", (value, enrollment_id))
                    conn.commit()
                
                cursor.close()
                conn.close()
                return jsonify({'success': True, 'message': 'Update successful'})
                
            except Exception as e:
                return jsonify({'success': False, 'message': f'Update failed: {str(e)}'}), 400
        
        # Get parameters
        academic_year = request.args.get('year', '2025-2026')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        debug = request.args.get('debug', '') == '1'
        export = request.args.get('export', '')
        
        per_page_options = [10, 25, 50, 100]
        if per_page not in per_page_options:
            per_page = 10
        
        offset = (page - 1) * per_page
        
        # Get available academic years
        cursor.execute("SELECT DISTINCT year FROM academic_year ORDER BY year DESC")
        available_years = [row['year'] for row in cursor.fetchall()]
        if not available_years:
            available_years = [str(datetime.now().year)]
        
        # Get all grades for dropdown
        cursor.execute("SELECT id, level FROM grade ORDER BY level ASC")
        all_grades = cursor.fetchall()
        
        # Get table columns for dynamic joining
        student_columns = get_table_columns(conn, 'student')
        enrollment_columns = get_table_columns(conn, 'enrollment')
        
        # Determine correct column names for joining
        student_id_column = 'RN' if 'RN' in student_columns else ('id' if 'id' in student_columns else 'ID')
        enrollment_student_column = 'student_RN' if 'student_RN' in enrollment_columns else ('student_id' if 'student_id' in enrollment_columns else ('RN' if 'RN' in enrollment_columns else 'student_RN'))
        
        # Build query
        query = """
            SELECT 
                e.*, 
                s.fullname as student_name,
                s.RN,
                COALESCE(g.level, 'N/A') as grade_level,
                COALESCE(sec.sec_name, 'N/A') as section_name,
                COALESCE(ay.year, 'N/A') as academic_year_value
            FROM enrollment e
            LEFT JOIN student s ON e.{} = s.{}
            LEFT JOIN grade g ON e.grade_id = g.id
            LEFT JOIN section sec ON e.section_id = sec.id
            LEFT JOIN academic_year ay ON e.academic_year_id = ay.id
            WHERE ay.year = %s
        """.format(enrollment_student_column, student_id_column)
        
        params = [academic_year]
        count_params = [academic_year]
        
        # Add search filter
        if search:
            search_conditions = [
                "s.fullname LIKE %s",
                "s.RN LIKE %s",
                "g.level LIKE %s",
                "sec.sec_name LIKE %s",
                "e.studid LIKE %s"
            ]
            query += " AND (" + " OR ".join(search_conditions) + ")"
            search_param = f'%{search}%'
            params.extend([search_param] * 5)
            count_params.extend([search_param] * 5)
        
        # Order by grade from studid, then section, then name
        query += """
            ORDER BY 
                CAST(
                    SUBSTRING_INDEX(
                        SUBSTRING_INDEX(e.studid, '/', 3), 
                        '/', 
                        -1
                    ) AS UNSIGNED
                ),
                sec.sec_name ASC,
                s.fullname ASC
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, offset])
        
        # Execute main query
        cursor.execute(query, params)
        enrollments = cursor.fetchall()
        
        # Get total count for pagination
        count_query = """
            SELECT COUNT(*) as total 
            FROM enrollment e
            LEFT JOIN student s ON e.{} = s.{}
            LEFT JOIN grade g ON e.grade_id = g.id
            LEFT JOIN section sec ON e.section_id = sec.id
            LEFT JOIN academic_year ay ON e.academic_year_id = ay.id
            WHERE ay.year = %s
        """.format(enrollment_student_column, student_id_column)
        
        if search:
            count_query += " AND (" + " OR ".join(search_conditions) + ")"
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()['total']
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        # Get primary key field
        cursor.execute("SHOW COLUMNS FROM enrollment")
        columns = cursor.fetchall()
        primary_key_field = 'id'
        for col in columns:
            if col['Key'] == 'PRI':
                primary_key_field = col['Field']
                break
        
        # Handle exports
        if export:
            # Build export query
            export_query = """
                SELECT 
                    e.*, 
                    s.fullname as student_name,
                    s.RN,
                    COALESCE(g.level, 'N/A') as grade_level,
                    COALESCE(sec.sec_name, 'N/A') as section_name,
                    COALESCE(ay.year, 'N/A') as academic_year_value
                FROM enrollment e
                LEFT JOIN student s ON e.{} = s.{}
                LEFT JOIN grade g ON e.grade_id = g.id
                LEFT JOIN section sec ON e.section_id = sec.id
                LEFT JOIN academic_year ay ON e.academic_year_id = ay.id
                WHERE ay.year = %s
            """.format(enrollment_student_column, student_id_column)
            
            export_params = [academic_year]
            
            if search:
                export_query += " AND (" + " OR ".join(search_conditions) + ")"
                export_params.extend([f'%{search}%'] * 5)
            
            export_query += """
                ORDER BY 
                    CAST(
                        SUBSTRING_INDEX(
                            SUBSTRING_INDEX(e.studid, '/', 3), 
                            '/', 
                            -1
                        ) AS UNSIGNED
                    ),
                    sec.sec_name ASC,
                    s.fullname ASC
            """
            
            cursor.execute(export_query, export_params)
            export_data = cursor.fetchall()
            
            if export == 'csv':
                return export_to_csv(export_data, academic_year)
        
        cursor.close()
        conn.close()
        
        # Prepare data for template
        counter = offset + 1
        enrollments_data = []
        for enrollment in enrollments:
            studid_parts = parse_stud_id(enrollment.get('studid'))
            enrollments_data.append({
                'counter': counter,
                'id': enrollment.get(primary_key_field),
                'rn': enrollment.get('RN', 'N/A'),
                'studid': enrollment.get('studid', ''),
                'studid_display': enrollment.get('studid', 'N/A') or 'N/A',
                'studid_parts_grade': studid_parts['grade'],
                'studid_parts_section': studid_parts['section'],
                'studid_parts_number': studid_parts['number'],
                'student_name': enrollment.get('student_name', 'N/A') or 'N/A',
                'grade_level': enrollment.get('grade_level', 'N/A'),
                'grade_id': enrollment.get('grade_id'),
                'section_id': enrollment.get('section_id', 'N/A'),
                'section_name': enrollment.get('section_name', 'N/A'),
                'academic_year_value': enrollment.get('academic_year_value', 'N/A'),
                'status': enrollment.get('status', ''),
                'has_status': bool(enrollment.get('status'))
            })
            counter += 1
        
        # Generate page range for pagination
        page_range = []
        max_visible = 5
        half = max_visible // 2
        start_page = max(1, page - half)
        end_page = min(total_pages, start_page + max_visible - 1)
        
        if end_page - start_page + 1 < max_visible:
            start_page = max(1, end_page - max_visible + 1)
        
        if start_page > 1:
            page_range.append(1)
            if start_page > 2:
                page_range.append('...')
        
        for i in range(start_page, end_page + 1):
            page_range.append(i)
        
        if end_page < total_pages:
            if end_page < total_pages - 1:
                page_range.append('...')
            page_range.append(total_pages)
        
        # Build query helper function
        def build_query(additional_params):
            query_params = {}
            if search:
                query_params['search'] = search
            if academic_year:
                query_params['year'] = academic_year
            if per_page:
                query_params['per_page'] = per_page
            if debug:
                query_params['debug'] = '1'
            if 'export' in additional_params:
                query_params['export'] = additional_params['export']
            if 'page' in additional_params:
                query_params['page'] = additional_params['page']
            return '&'.join([f"{k}={v}" for k, v in query_params.items()])
        
        return render_template_string(
            get_html_template(),
            enrollments=enrollments_data,
            all_grades=all_grades,
            available_years=available_years,
            academic_year=academic_year,
            search=search,
            page=page,
            per_page=per_page,
            per_page_options=per_page_options,
            total_count=total_count,
            total_pages=total_pages,
            page_range=page_range,
            debug=debug,
            build_query=build_query,
            total_students=total_count
        )
        
    except mysql.connector.Error as e:
        return f"<h1>Database Error</h1><p>{str(e)}</p>"


def export_to_csv(export_data, academic_year):
    """Export enrollment data to CSV"""
    output = StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['#', 'RN', 'Student ID', 'Full Name', 'Level', 'Section ID', 'Section', 'Year', 'Status', 'Date'])
    
    # Write data
    for idx, row in enumerate(export_data, 1):
        writer.writerow([
            idx,
            row.get('RN', ''),
            row.get('studid', ''),
            row.get('student_name', ''),
            row.get('grade_level', ''),
            row.get('section_id', ''),
            row.get('section_name', ''),
            row.get('yearly_order', ''),
            row.get('academic_year_value', ''),
            row.get('status', ''),
            row.get('enrollment_date', '')
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=enrollment_{academic_year}.csv'
    return response


def get_html_template():
    """Return the HTML template as a string - NARROWER WIDTH"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enrollment Data - Academic Year {{ academic_year }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; color: #333; line-height: 1.6; }
        
        /* NARROWER CONTAINER */
        .container { max-width: 1100px; margin: 0 auto; padding: 20px; }
        
        h1 { text-align: center; color: #2c3e50; margin-bottom: 30px; font-size: 2.2em; }
        
        /* Debug Panel */
        .debug-panel { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #f5c6cb; font-family: monospace; display: none; }
        .debug-panel.visible { display: block; }
        
        /* Year Selector */
        .year-selector { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; text-align: center; }
        .year-selector label { font-weight: bold; margin-right: 10px; font-size: 1em; }
        .year-selector select { padding: 8px 12px; border: 2px solid #ddd; border-radius: 5px; font-size: 0.95em; background: white; cursor: pointer; }
        .year-selector select:hover { border-color: #3498db; }
        
        /* Controls */
        .controls { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .search-box { flex: 2; min-width: 250px; display: flex; gap: 10px; }
        .search-box input { flex: 1; padding: 8px 12px; border: 2px solid #ddd; border-radius: 5px; font-size: 0.9em; }
        .search-box button { padding: 8px 15px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 0.9em; }
        .search-box button:hover { background: #2980b9; }
        .per-page { flex: 1; min-width: 180px; display: flex; align-items: center; gap: 8px; justify-content: flex-end; }
        .per-page label { font-weight: bold; white-space: nowrap; font-size: 0.9em; }
        .per-page select { padding: 8px 12px; border: 2px solid #ddd; border-radius: 5px; font-size: 0.9em; background: white; cursor: pointer; }
        .btn { padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; font-size: 0.9em; }
        .btn-danger { background: #dc3545; color: white; }
        
        /* Summary */
        .summary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .stats { display: flex; justify-content: space-around; flex-wrap: wrap; gap: 15px; margin-top: 10px; }
        .stats span { background: rgba(255,255,255,0.2); padding: 10px 20px; border-radius: 8px; font-weight: bold; font-size: 1em; }
        
        /* Table - NARROWER with better column sizing */
        .table-container { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; overflow-x: auto; }
        .enrollment-table { width: 100%; border-collapse: collapse; font-size: 0.85em; }
        .enrollment-table th { background: #34495e; color: white; padding: 10px 8px; text-align: left; font-weight: 600; }
        .enrollment-table td { padding: 8px; border-bottom: 1px solid #ddd; }
        .enrollment-table tbody tr:hover { background-color: #f8f9fa; }
        .enrollment-table tbody tr:nth-child(even) { background-color: #f8f9fa; }
        
        /* Column widths */
        .enrollment-table th:nth-child(1) { width: 40px; }
        .enrollment-table th:nth-child(2) { width: 70px; }
        .enrollment-table th:nth-child(3) { width: 110px; }
        .enrollment-table th:nth-child(4) { width: 160px; }
        .enrollment-table th:nth-child(5) { width: 50px; }
        .enrollment-table th:nth-child(6) { width: 70px; }
        .enrollment-table th:nth-child(7) { width: 100px; }
        .enrollment-table th:nth-child(8) { width: 70px; }
        .enrollment-table th:nth-child(9) { width: 90px; }
        
        /* Editable cells */
        .editable { cursor: pointer; transition: background-color 0.2s; position: relative; }
        .editable:hover { background-color: #e3f2fd; }
        .editable .edit-mode { display: none; width: 100%; padding: 6px; border: 2px solid #3498db; border-radius: 4px; font-size: 0.85em; }
        .editable.editing .view-mode { display: none; }
        .editable.editing .edit-mode { display: block; }
        
        /* Status badges */
        .status { padding: 4px 8px; border-radius: 15px; font-size: 0.75em; font-weight: 600; text-transform: uppercase; display: inline-block; }
        .status.promoted { background-color: #d4edda; color: #28a745; border: 1px solid #c3e6cb; }
        .status.repeated { background-color: #f8d7da; color: #dc3545; border: 1px solid #f5c6cb; }
        .status.new { background-color: #e2e3e5; color: #212529; border: 1px solid #d6d8db; }
        
        .missing-data { color: #dc3545; font-style: italic; font-size: 0.8em; }
        .studid-parts { font-size: 0.7em; color: #6c757d; margin-top: 2px; }
        
        /* Notification */
        .notification { position: fixed; top: 20px; right: 20px; padding: 12px 18px; border-radius: 5px; color: white; font-weight: 600; font-size: 0.9em; z-index: 1000; opacity: 0; transform: translateX(100%); transition: all 0.3s ease; }
        .notification.show { opacity: 1; transform: translateX(0); }
        .notification.success { background-color: #28a745; }
        .notification.error { background-color: #dc3545; }
        
        /* Pagination */
        .pagination { display: flex; justify-content: center; margin-top: 20px; gap: 5px; flex-wrap: wrap; }
        .pagination a, .pagination span { display: inline-block; padding: 6px 12px; border: 1px solid #ddd; border-radius: 5px; text-decoration: none; color: #3498db; font-weight: 600; font-size: 0.85em; }
        .pagination a:hover { background: #3498db; color: white; }
        .pagination span.current { background: #3498db; color: white; border-color: #3498db; }
        .pagination-info { text-align: center; margin-top: 10px; color: #6c757d; font-size: 0.85em; }
        
        /* Export buttons */
        .export-section { text-align: center; margin-top: 20px; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
        .export-btn { display: inline-flex; align-items: center; gap: 5px; padding: 10px 18px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; font-weight: 600; font-size: 0.9em; transition: all 0.3s; }
        .export-btn.csv { background: #6c757d; }
        .export-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        
        .no-data { text-align: center; padding: 40px; background: white; border-radius: 8px; }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .stats { flex-direction: column; align-items: center; }
            .controls { flex-direction: column; align-items: stretch; }
            .per-page { justify-content: flex-start; }
            .enrollment-table { font-size: 0.75em; }
            .enrollment-table th, .enrollment-table td { padding: 6px 4px; }
        }
        
        @media print {
            .year-selector, .controls, .export-section, .pagination, .pagination-info, .debug-panel { display: none; }
            body { background-color: white; }
            .table-container { box-shadow: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Enrollment Data</h1>
        
        {% if debug %}
        <div class="debug-panel visible">
            <strong>Debug Information:</strong><br>
            Academic Year: {{ academic_year }}<br>
            Total Records: {{ total_students }}<br>
            Current Page: {{ page }}<br>
            Records Per Page: {{ per_page }}<br>
        </div>
        {% endif %}
        
        <div id="notification" class="notification"></div>
        
        <!-- Year Selector -->
        <div class="year-selector">
            <form method="GET" action="">
                <label for="year">📅 Select Academic Year:</label>
                <select name="year" id="year" onchange="this.form.submit()">
                    {% for year in available_years %}
                        <option value="{{ year }}" {% if year == academic_year %}selected{% endif %}>{{ year }}</option>
                    {% endfor %}
                </select>
                <input type="hidden" name="search" value="{{ search }}">
                <input type="hidden" name="per_page" value="{{ per_page }}">
                {% if debug %}<input type="hidden" name="debug" value="1">{% endif %}
            </form>
        </div>
        
        <!-- Controls -->
        <div class="controls">
            <div class="search-box">
                <form method="GET" action="" style="display: flex; gap: 10px; width: 100%;">
                    <input type="text" name="search" placeholder="🔍 Search by name, RN, level, section, or student ID..." value="{{ search }}">
                    <input type="hidden" name="year" value="{{ academic_year }}">
                    <input type="hidden" name="per_page" value="{{ per_page }}">
                    {% if debug %}<input type="hidden" name="debug" value="1">{% endif %}
                    <button type="submit"><i class="fas fa-search"></i> Search</button>
                    {% if search %}
                        <a href="?year={{ academic_year }}&per_page={{ per_page }}{% if debug %}&debug=1{% endif %}" class="btn btn-danger"><i class="fas fa-times"></i> Clear</a>
                    {% endif %}
                </form>
            </div>
            <div class="per-page">
                <label for="per_page">Show:</label>
                <select name="per_page" id="per_page" onchange="changePerPage(this.value)">
                    {% for option in per_page_options %}
                        <option value="{{ option }}" {% if option == per_page %}selected{% endif %}>{{ option }} records</option>
                    {% endfor %}
                </select>
            </div>
        </div>
        
        <!-- Summary -->
        <div class="summary">
            <div class="stats">
                <span>👨‍🎓 Total Students: {{ total_students }}</span>
                <span>📄 Page {{ page }} of {{ total_pages }}</span>
                <span>📊 Showing {{ per_page }} per page</span>
            </div>
        </div>
        
        {% if total_students > 0 %}
        <div class="table-container">
            <table class="enrollment-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>RN</th>
                        <th>Student ID</th>
                        <th>Full Name</th>
                        <th>Level</th>
                        <th>Sec ID</th>
                        <th>Section</th>
                        <th>Year</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for enrollment in enrollments %}
                    <tr id="row-{{ enrollment.id }}">
                        <td>{{ enrollment.counter }}</span>
                        <td>{{ enrollment.rn }}</span>
                        <td class="editable" data-id="{{ enrollment.id }}" data-field="studid">
                            <span class="view-mode">
                                {% if enrollment.studid_display == 'N/A' or not enrollment.studid_display %}
                                    <span class="missing-data">N/A</span>
                                {% else %}
                                    {{ enrollment.studid_display }}
                                    {% if debug %}
                                    <div class="studid-parts">
                                        G:{{ enrollment.studid_parts_grade }} | S:{{ enrollment.studid_parts_section }} | #:{{ enrollment.studid_parts_number }}
                                    </div>
                                    {% endif %}
                                {% endif %}
                            </span>
                            <input type="text" class="edit-mode" value="{{ enrollment.studid }}">
                        </span>
                        <td class="student-name">{{ enrollment.student_name|truncate(25) }}</td>
                        <td class="editable" data-id="{{ enrollment.id }}" data-field="grade_id">
                            <span class="view-mode">{{ enrollment.grade_level }}</span>
                            <select class="edit-mode">
                                {% for grade in all_grades %}
                                    <option value="{{ grade.id }}" {% if grade.id == enrollment.grade_id %}selected{% endif %}>{{ grade.level }}</option>
                                {% endfor %}
                            </select>
                        </span>
                        <td class="editable" data-id="{{ enrollment.id }}" data-field="section_id">
                            <span class="view-mode">{{ enrollment.section_id }}</span>
                            <input type="text" class="edit-mode" value="{{ enrollment.section_id }}">
                        </span>
                        <td class="editable" data-id="{{ enrollment.id }}" data-field="section_name">
                            <span class="view-mode">{{ enrollment.section_name }}</span>
                            <input type="text" class="edit-mode" value="{{ enrollment.section_name }}">
                        </span>
                        <td>{{ enrollment.academic_year_value }}</span>
                        <td class="editable" data-id="{{ enrollment.id }}" data-field="status">
                            <span class="view-mode">
                                {% if enrollment.has_status %}
                                    <span class="status {{ enrollment.status.lower() }}">{{ enrollment.status }}</span>
                                {% else %}
                                    <span class="missing-data">N/A</span>
                                {% endif %}
                            </span>
                            <select class="edit-mode">
                                <option value="PROMOTED" {% if enrollment.status == 'PROMOTED' %}selected{% endif %}>PROMOTED</option>
                                <option value="REPEATED" {% if enrollment.status == 'REPEATED' %}selected{% endif %}>REPEATED</option>
                                <option value="NEW" {% if enrollment.status == 'NEW' %}selected{% endif %}>NEW</option>
                                <option value="ACTIVE" {% if enrollment.status == 'ACTIVE' %}selected{% endif %}>ACTIVE</option>
                                <option value="INACTIVE" {% if enrollment.status == 'INACTIVE' %}selected{% endif %}>INACTIVE</option>
                            </select>
                        </span>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="pagination-info">
            Showing {{ (page - 1) * per_page + 1 }} to {{ [page * per_page, total_students]|min }} of {{ total_students }} records
        </div>
        
        {% if total_pages > 1 %}
        <div class="pagination">
            {% if page > 1 %}
                <a href="?{{ build_query({'page': page - 1}) }}">« Prev</a>
            {% endif %}
            {% for p in page_range %}
                {% if p == page %}
                    <span class="current">{{ p }}</span>
                {% elif p == '...' %}
                    <span>...</span>
                {% else %}
                    <a href="?{{ build_query({'page': p}) }}">{{ p }}</a>
                {% endif %}
            {% endfor %}
            {% if page < total_pages %}
                <a href="?{{ build_query({'page': page + 1}) }}">Next »</a>
            {% endif %}
        </div>
        {% endif %}
        
        <div class="export-section">
            <a href="?{{ build_query({'export': 'csv'}) }}" class="export-btn csv"><i class="fas fa-file-csv"></i> Export CSV</a>
            <a href="javascript:window.print()" class="export-btn"><i class="fas fa-print"></i> Print</a>
        </div>
        {% else %}
        <div class="no-data">
            <p>📭 No enrollment data found for academic year {{ academic_year }}</p>
        </div>
        {% endif %}
    </div>
    
    <script>
        function showNotification(message, type) {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification show ${type}`;
            setTimeout(() => notification.classList.remove('show'), 3000);
        }
        
        function changePerPage(value) {
            const url = new URL(window.location.href);
            url.searchParams.set('per_page', value);
            url.searchParams.set('page', '1');
            window.location.href = url.toString();
        }
        
        document.querySelectorAll('.editable').forEach(cell => {
            cell.addEventListener('click', function() {
                if (this.classList.contains('editing')) return;
                
                const viewMode = this.querySelector('.view-mode');
                const editMode = this.querySelector('.edit-mode');
                if (!editMode) return;
                
                this.classList.add('editing');
                viewMode.style.display = 'none';
                editMode.style.display = 'block';
                editMode.focus();
                
                let isSaving = false;
                
                const saveChanges = () => {
                    if (isSaving) return;
                    isSaving = true;
                    
                    const newValue = editMode.value;
                    const enrollmentId = this.getAttribute('data-id');
                    const field = this.getAttribute('data-field');
                    
                    const textValue = editMode.tagName === 'SELECT' ? 
                                      editMode.options[editMode.selectedIndex].text : 
                                      newValue;
                    
                    const formData = new URLSearchParams();
                    formData.append('update_enrollment', '1');
                    formData.append('enrollment_id', enrollmentId);
                    formData.append('field', field);
                    formData.append('value', newValue);
                    
                    fetch(window.location.href, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            viewMode.textContent = textValue;
                            showNotification('Update successful', 'success');
                        } else {
                            showNotification(data.message, 'error');
                        }
                        this.classList.remove('editing');
                        viewMode.style.display = 'block';
                        editMode.style.display = 'none';
                        isSaving = false;
                    })
                    .catch(err => {
                        showNotification('Network error', 'error');
                        isSaving = false;
                    });
                };
                
                if (editMode.tagName === 'SELECT') {
                    editMode.onchange = saveChanges;
                    editMode.onblur = () => {
                        this.classList.remove('editing');
                        viewMode.style.display = 'block';
                        editMode.style.display = 'none';
                    };
                } else {
                    editMode.onblur = saveChanges;
                    editMode.onkeydown = (e) => { if (e.key === 'Enter') saveChanges(); };
                }
            });
        });
    </script>
</body>
</html>
    '''