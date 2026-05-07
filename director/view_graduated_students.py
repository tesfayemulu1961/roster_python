from flask import Blueprint, session, redirect, request, render_template_string, make_response
from functools import wraps
import mysql.connector
import sys
import os
from datetime import datetime
import csv
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
view_graduated_students_bp = Blueprint('view_graduated_students', __name__, url_prefix='/director')

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

@view_graduated_students_bp.route('/view_graduated_students')
@login_required
def view_graduated_students():
    """Display graduated students (Grade 8 completers)"""
    
    # Only directors should access this
    if session.get('user_type') != 'director':
        return redirect('/unauthorized')
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get parameters
        search_query = request.args.get('search', '').strip()
        academic_year_filter = request.args.get('academic_year', '').strip()
        export = request.args.get('export', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 15
        offset = (page - 1) * per_page
        
        # Exclude current academic year (2025-2026)
        exclude_year = '2025-2026'
        
        # Get all academic years except current for filter dropdown
        cursor.execute("""
            SELECT id, year FROM academic_year 
            WHERE year != %s 
            ORDER BY year DESC
        """, (exclude_year,))
        academic_years = cursor.fetchall()
        
        # Build base query parts
        select_fields = """
            s.rn, 
            s.fullname, 
            s.gender,
            s.age,
            g.level as grade_level,
            sec.sec_name as section_name,
            ay.year as academic_year,
            ay.id as academic_year_id
        """
        
        from_clause = """
            FROM student s
            LEFT JOIN grade g ON s.grade_id = g.id
            LEFT JOIN section sec ON s.section_id = sec.id
            LEFT JOIN academic_year ay ON s.academic_year_id = ay.id
        """
        
        where_clause = " WHERE s.grade_id = 12 AND ay.year != %s"
        params = [exclude_year]
        
        # Add academic year filter
        if academic_year_filter:
            cursor.execute("SELECT year FROM academic_year WHERE id = %s", (academic_year_filter,))
            selected_year = cursor.fetchone()
            if selected_year and selected_year['year'] != exclude_year:
                where_clause += " AND ay.id = %s"
                params.append(academic_year_filter)
        
        # Add search filter
        if search_query:
            where_clause += " AND (s.fullname LIKE %s OR s.rn LIKE %s OR sec.sec_name LIKE %s)"
            search_param = f'%{search_query}%'
            params.extend([search_param, search_param, search_param])
        
        # Handle CSV export
        if export == 'csv':
            export_query = f"SELECT {select_fields} {from_clause} {where_clause} ORDER BY ay.year DESC, s.fullname"
            cursor.execute(export_query, params)
            export_data = cursor.fetchall()
            cursor.close()
            conn.close()
            return export_to_csv(export_data)
        
        # Get total count for pagination
        count_query = f"SELECT COUNT(*) as total {from_clause} {where_clause}"
        cursor.execute(count_query, params)
        count_result = cursor.fetchone()
        total_count = count_result['total'] if count_result else 0
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        # Get paginated data
        data_query = f"SELECT {select_fields} {from_clause} {where_clause} ORDER BY ay.year DESC, s.fullname LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        cursor.execute(data_query, params)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Format students data
        students = []
        counter = offset + 1
        for row in rows:
            age_formatted = 'N/A'
            if row.get('age'):
                try:
                    if isinstance(row['age'], datetime):
                        age_formatted = row['age'].strftime('%b %d, %Y')
                    else:
                        age_formatted = str(row['age'])
                except:
                    age_formatted = str(row['age'])
            
            students.append({
                'counter': counter,
                'rn': row.get('rn', 'N/A'),
                'fullname': row.get('fullname', 'N/A'),
                'gender': row.get('gender', 'N/A') or 'N/A',
                'age_formatted': age_formatted,
                'grade_level': row.get('grade_level', 'N/A'),
                'section_name': row.get('section_name'),
                'academic_year': row.get('academic_year')
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
            if search_query:
                query_params['search'] = search_query
            if academic_year_filter:
                query_params['academic_year'] = academic_year_filter
            if 'export' in additional_params and additional_params['export']:
                query_params['export'] = additional_params['export']
            if 'page' in additional_params:
                query_params['page'] = additional_params['page']
            return '&'.join([f"{k}={v}" for k, v in query_params.items()])
        
        # HTML TEMPLATE - NARROWER WIDTH (900px)
        html_template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Graduated Students - Grade 8</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 0;
                    padding: 20px;
                    background: #f0f2f5;
                }
                
                /* NARROWER CONTAINER - 900px */
                .container {
                    max-width: 900px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    padding: 20px;
                }
                
                table { 
                    border-collapse: collapse; 
                    width: 100%; 
                    font-size: 14px;
                }
                th, td { 
                    border: 1px solid #ddd; 
                    padding: 8px; 
                    text-align: left; 
                }
                th { 
                    background-color: #4CAF50; 
                    color: white; 
                }
                .pagination { 
                    margin: 20px 0; 
                    text-align: center; 
                }
                .pagination a, .pagination span { 
                    display: inline-block; 
                    padding: 5px 10px; 
                    margin: 0 2px; 
                    text-decoration: none; 
                    border: 1px solid #ddd; 
                }
                .pagination span.current { 
                    background-color: #4CAF50; 
                    color: white; 
                    border-color: #4CAF50; 
                }
                .export-btn { 
                    display: inline-block; 
                    padding: 10px 20px; 
                    margin: 10px; 
                    background-color: #4CAF50; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                }
                .stats { 
                    margin: 20px 0; 
                    padding: 10px; 
                    background: #f0f0f0; 
                    border-radius: 5px;
                }
                h1 {
                    margin-top: 0;
                    font-size: 1.8em;
                }
                .table-wrapper {
                    overflow-x: auto;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎓 Graduated Students - Grade 8</h1>
                
                <div class="stats">
                    <strong>Total Graduates: {{ total_count }}</strong> | 
                    Page {{ page }} of {{ total_pages }} | 
                    Showing 15 per page
                </div>
                
                <!-- DATA TABLE -->
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>RN</th>
                                <th>Full Name</th>
                                <th>Gender</th>
                                <th>Age</th>
                                <th>Grade</th>
                                <th>Section</th>
                                <th>Academic Year</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for student in students %}
                            <tr>
                                <td>{{ student.counter }}</span>
                                <td>{{ student.rn }}</span>
                                <td>{{ student.fullname }}</span>
                                <td>{{ student.gender }}</span>
                                <td>{{ student.age_formatted }}</span>
                                <td>{{ student.grade_level }}</span>
                                <td>{{ student.section_name or 'N/A' }}</span>
                                <td>{{ student.academic_year or 'N/A' }}</span>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                
                <!-- PAGINATION - ONLY AT THE BOTTOM -->
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
                
                <!-- EXPORT BUTTONS AT BOTTOM -->
                <div style="text-align: center; margin-top: 20px;">
                    <a href="?{{ build_query({'export': 'csv'}) }}" class="export-btn">📊 Export CSV</a>
                    <a href="javascript:window.print()" class="export-btn">🖨️ Print</a>
                </div>
                
                <p style="margin-top: 20px; color: green; text-align: center; font-size: 12px;">
                    ✓ PAGINATION IS ONLY AT THE BOTTOM (below the table)
                </p>
            </div>
        </body>
        </html>
        '''
        
        return render_template_string(
            html_template,
            students=students,
            academic_years=academic_years,
            academic_year_filter=academic_year_filter,
            search_query=search_query,
            total_count=total_count,
            page=page,
            total_pages=total_pages,
            page_range=page_range,
            build_query=build_query
        )
        
    except mysql.connector.Error as e:
        return f"<h1>Database Error</h1><p>{str(e)}</p>"


def export_to_csv(export_data):
    """Export data to CSV file"""
    output = StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['#', 'Student RN', 'Full Name', 'Gender', 'Age', 'Grade', 'Section', 'Academic Year'])
    
    for idx, row in enumerate(export_data, 1):
        age_formatted = 'N/A'
        if row.get('age'):
            try:
                if isinstance(row['age'], datetime):
                    age_formatted = row['age'].strftime('%b %d, %Y')
                else:
                    age_formatted = str(row['age'])
            except:
                age_formatted = str(row['age'])
        
        writer.writerow([
            idx,
            row.get('rn', 'N/A'),
            row.get('fullname', 'N/A'),
            row.get('gender', 'N/A') or 'N/A',
            age_formatted,
            row.get('grade_level', 'N/A'),
            row.get('section_name') or 'N/A',
            row.get('academic_year') or 'N/A'
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=graduated_students_grade8.csv'
    return response