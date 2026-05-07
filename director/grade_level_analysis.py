# grade_level_analysis.py
from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import re

grade_level_analysis_bp = Blueprint('grade_level_analysis', __name__, url_prefix='/director')

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

def get_grade_name(grade_id):
    """Map grade_id to display number 1-8"""
    grade_sequence = {
        5: '1', 6: '2', 7: '3', 8: '4',
        9: '5', 10: '6', 11: '7', 12: '8'
    }
    return grade_sequence.get(grade_id, str(grade_id))

def get_section_letter(sec_name):
    """Extract just the section letter (A,B,C...) from sec_name like '5 A', 'A', '5A'"""
    cleaned = re.sub(r'^\d+[\s\-_]*', '', str(sec_name)).strip()
    return cleaned if cleaned else sec_name

def process_semester_data(conn, academic_year_id, semester):
    """Process data for a specific semester"""
    cursor = conn.cursor(dictionary=True)
    
    # Get distinct grades ordered by position
    grades_query = """
        SELECT DISTINCT sc.grade_id
        FROM student_scores sc
        WHERE sc.academic_year_id = %s 
        ORDER BY 
            CASE sc.grade_id
                WHEN 5 THEN 1 WHEN 6 THEN 2 WHEN 7 THEN 3 WHEN 8 THEN 4
                WHEN 9 THEN 5 WHEN 10 THEN 6 WHEN 11 THEN 7 WHEN 12 THEN 8
                ELSE sc.grade_id
            END ASC
    """
    cursor.execute(grades_query, (academic_year_id,))
    grades_result = cursor.fetchall()
    
    sum_counter = 1
    grade_analysis = []
    grand_totals = {
        'registered': {'M': 0, 'F': 0, 'T': 0},
        'examined': {'M': 0, 'F': 0, 'T': 0},
        'lt50': {'M': 0, 'F': 0, 'T': 0},
        'lt50_pct': {'M': 0, 'F': 0, 'T': 0},
        'gte50': {'M': 0, 'F': 0, 'T': 0},
        'gte50_pct': {'M': 0, 'F': 0, 'T': 0},
        'gte75': {'M': 0, 'F': 0, 'T': 0},
        'gte75_pct': {'M': 0, 'F': 0, 'T': 0},
        'gte85': {'M': 0, 'F': 0, 'T': 0},
        'gte85_pct': {'M': 0, 'F': 0, 'T': 0}
    }
    
    for idx, grade_row in enumerate(grades_result, start=1):
        grade_id = grade_row['grade_id']
        grade_data = {
            'grade_name': str(idx),
            'sum_label': f'Sum{sum_counter}',
            'sections': {},
            'subtotals': {
                'registered': {'M': 0, 'F': 0, 'T': 0},
                'examined': {'M': 0, 'F': 0, 'T': 0},
                'lt50': {'M': 0, 'F': 0, 'T': 0},
                'lt50_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte50': {'M': 0, 'F': 0, 'T': 0},
                'gte50_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte75': {'M': 0, 'F': 0, 'T': 0},
                'gte75_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte85': {'M': 0, 'F': 0, 'T': 0},
                'gte85_pct': {'M': 0, 'F': 0, 'T': 0}
            }
        }
        sum_counter += 1
        
        # Get sections for this grade
        sections_query = """
            SELECT DISTINCT s.sec_name 
            FROM section s
            JOIN student_scores sc ON s.ID = sc.section_id
            WHERE sc.grade_id = %s AND sc.academic_year_id = %s
            ORDER BY s.sec_name ASC
        """
        cursor.execute(sections_query, (grade_id, academic_year_id))
        sections_result = cursor.fetchall()
        
        for section_row in sections_result:
            section_name = section_row['sec_name']
            
            # Get students for this section
            students_query = """
                SELECT s.gender, 
                    (sc.Amh + sc.Eng + sc.Maths + 
                        IFNULL(sc.EnSc, 0) + IFNULL(sc.Arts, 0) + 
                        IFNULL(sc.HPE, 0) + IFNULL(sc.Ethics, 0) + 
                        IFNULL(sc.GSc, 0) + IFNULL(sc.SSc, 0) + 
                        IFNULL(sc.Ctzp, 0) + IFNULL(sc.IT, 0) + 
                        IFNULL(sc.CTE, 0)) / 
                        (CASE 
                            WHEN sc.grade_id BETWEEN 11 AND 12 THEN 10 
                            ELSE 7 
                        END) as avg_score
                FROM student s
                JOIN student_scores sc ON s.RN = sc.student_RN
                JOIN section sec ON sc.section_id = sec.ID
                WHERE sc.grade_id = %s 
                AND sc.academic_year_id = %s
                AND sec.sec_name = %s
                AND sc.semester = %s
                GROUP BY s.RN, s.gender
            """
            cursor.execute(students_query, (grade_id, academic_year_id, section_name, semester))
            students_result = cursor.fetchall()
            
            section_data = {
                'section_name': section_name,
                'registered': {'M': 0, 'F': 0, 'T': 0},
                'examined': {'M': 0, 'F': 0, 'T': 0},
                'lt50': {'M': 0, 'F': 0, 'T': 0},
                'lt50_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte50': {'M': 0, 'F': 0, 'T': 0},
                'gte50_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte75': {'M': 0, 'F': 0, 'T': 0},
                'gte75_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte85': {'M': 0, 'F': 0, 'T': 0},
                'gte85_pct': {'M': 0, 'F': 0, 'T': 0}
            }
            
            for student in students_result:
                gender = student['gender']
                avg_score = student['avg_score']
                
                # Skip students with missing or invalid gender
                if gender not in ('M', 'F'):
                    continue
                
                # Update registered counts
                section_data['registered'][gender] += 1
                section_data['registered']['T'] += 1
                grade_data['subtotals']['registered'][gender] += 1
                grade_data['subtotals']['registered']['T'] += 1
                grand_totals['registered'][gender] += 1
                grand_totals['registered']['T'] += 1
                
                if avg_score is not None:
                    # Update examined counts
                    section_data['examined'][gender] += 1
                    section_data['examined']['T'] += 1
                    grade_data['subtotals']['examined'][gender] += 1
                    grade_data['subtotals']['examined']['T'] += 1
                    grand_totals['examined'][gender] += 1
                    grand_totals['examined']['T'] += 1
                    
                    if avg_score < 50:
                        section_data['lt50'][gender] += 1
                        section_data['lt50']['T'] += 1
                        grade_data['subtotals']['lt50'][gender] += 1
                        grade_data['subtotals']['lt50']['T'] += 1
                        grand_totals['lt50'][gender] += 1
                        grand_totals['lt50']['T'] += 1
                    else:
                        section_data['gte50'][gender] += 1
                        section_data['gte50']['T'] += 1
                        grade_data['subtotals']['gte50'][gender] += 1
                        grade_data['subtotals']['gte50']['T'] += 1
                        grand_totals['gte50'][gender] += 1
                        grand_totals['gte50']['T'] += 1
                        
                        if avg_score >= 75:
                            section_data['gte75'][gender] += 1
                            section_data['gte75']['T'] += 1
                            grade_data['subtotals']['gte75'][gender] += 1
                            grade_data['subtotals']['gte75']['T'] += 1
                            grand_totals['gte75'][gender] += 1
                            grand_totals['gte75']['T'] += 1
                            
                            if avg_score >= 85:
                                section_data['gte85'][gender] += 1
                                section_data['gte85']['T'] += 1
                                grade_data['subtotals']['gte85'][gender] += 1
                                grade_data['subtotals']['gte85']['T'] += 1
                                grand_totals['gte85'][gender] += 1
                                grand_totals['gte85']['T'] += 1
            
            # Calculate percentages for section
            for gender in ['M', 'F', 'T']:
                examined = section_data['examined'][gender]
                section_data['lt50_pct'][gender] = round((section_data['lt50'][gender] / examined * 100), 1) if examined > 0 else 0
                section_data['gte50_pct'][gender] = round((section_data['gte50'][gender] / examined * 100), 1) if examined > 0 else 0
                section_data['gte75_pct'][gender] = round((section_data['gte75'][gender] / examined * 100), 1) if examined > 0 else 0
                section_data['gte85_pct'][gender] = round((section_data['gte85'][gender] / examined * 100), 1) if examined > 0 else 0
            
            grade_data['sections'][section_name] = section_data
        
        # Calculate percentages for grade subtotals
        for gender in ['M', 'F', 'T']:
            examined = grade_data['subtotals']['examined'][gender]
            grade_data['subtotals']['lt50_pct'][gender] = round((grade_data['subtotals']['lt50'][gender] / examined * 100), 1) if examined > 0 else 0
            grade_data['subtotals']['gte50_pct'][gender] = round((grade_data['subtotals']['gte50'][gender] / examined * 100), 1) if examined > 0 else 0
            grade_data['subtotals']['gte75_pct'][gender] = round((grade_data['subtotals']['gte75'][gender] / examined * 100), 1) if examined > 0 else 0
            grade_data['subtotals']['gte85_pct'][gender] = round((grade_data['subtotals']['gte85'][gender] / examined * 100), 1) if examined > 0 else 0
        
        grade_analysis.append(grade_data)
    
    # Calculate percentages for grand totals
    for gender in ['M', 'F', 'T']:
        examined = grand_totals['examined'][gender]
        grand_totals['lt50_pct'][gender] = round((grand_totals['lt50'][gender] / examined * 100), 1) if examined > 0 else 0
        grand_totals['gte50_pct'][gender] = round((grand_totals['gte50'][gender] / examined * 100), 1) if examined > 0 else 0
        grand_totals['gte75_pct'][gender] = round((grand_totals['gte75'][gender] / examined * 100), 1) if examined > 0 else 0
        grand_totals['gte85_pct'][gender] = round((grand_totals['gte85'][gender] / examined * 100), 1) if examined > 0 else 0
    
    cursor.close()
    return {
        'grade_analysis': grade_analysis,
        'grand_totals': grand_totals
    }

def calculate_average_data(first_semester_data, second_semester_data):
    """Calculate average between first and second semester"""
    average_data = {
        'grade_analysis': [],
        'grand_totals': {
            'registered': {'M': 0, 'F': 0, 'T': 0},
            'examined': {'M': 0, 'F': 0, 'T': 0},
            'lt50': {'M': 0, 'F': 0, 'T': 0},
            'lt50_pct': {'M': 0, 'F': 0, 'T': 0},
            'gte50': {'M': 0, 'F': 0, 'T': 0},
            'gte50_pct': {'M': 0, 'F': 0, 'T': 0},
            'gte75': {'M': 0, 'F': 0, 'T': 0},
            'gte75_pct': {'M': 0, 'F': 0, 'T': 0},
            'gte85': {'M': 0, 'F': 0, 'T': 0},
            'gte85_pct': {'M': 0, 'F': 0, 'T': 0}
        }
    }
    
    for index, grade in enumerate(first_semester_data['grade_analysis']):
        avg_grade = {
            'grade_name': grade['grade_name'],
            'sum_label': grade['sum_label'],
            'sections': {},
            'subtotals': {
                'registered': {'M': 0, 'F': 0, 'T': 0},
                'examined': {'M': 0, 'F': 0, 'T': 0},
                'lt50': {'M': 0, 'F': 0, 'T': 0},
                'lt50_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte50': {'M': 0, 'F': 0, 'T': 0},
                'gte50_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte75': {'M': 0, 'F': 0, 'T': 0},
                'gte75_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte85': {'M': 0, 'F': 0, 'T': 0},
                'gte85_pct': {'M': 0, 'F': 0, 'T': 0}
            }
        }
        
        second_grade = second_semester_data['grade_analysis'][index] if index < len(second_semester_data['grade_analysis']) else grade
        
        for section_name, section in grade['sections'].items():
            section2 = second_grade['sections'].get(section_name, section)
            
            avg_section = {
                'section_name': section_name,
                'registered': {'M': 0, 'F': 0, 'T': 0},
                'examined': {'M': 0, 'F': 0, 'T': 0},
                'lt50': {'M': 0, 'F': 0, 'T': 0},
                'lt50_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte50': {'M': 0, 'F': 0, 'T': 0},
                'gte50_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte75': {'M': 0, 'F': 0, 'T': 0},
                'gte75_pct': {'M': 0, 'F': 0, 'T': 0},
                'gte85': {'M': 0, 'F': 0, 'T': 0},
                'gte85_pct': {'M': 0, 'F': 0, 'T': 0}
            }
            
            # Calculate averages for numeric metrics
            for metric in ['registered', 'examined', 'lt50', 'gte50', 'gte75', 'gte85']:
                for gender in ['M', 'F']:
                    avg_val = round((section[metric][gender] + section2[metric][gender]) / 2)
                    avg_section[metric][gender] = avg_val
                avg_section[metric]['T'] = avg_section[metric]['M'] + avg_section[metric]['F']
                
                # Accumulate to grade subtotals
                for gender in ['M', 'F', 'T']:
                    avg_grade['subtotals'][metric][gender] += avg_section[metric][gender]
            
            # Calculate percentages for this section
            for gender in ['M', 'F', 'T']:
                examined = avg_section['examined'][gender]
                avg_section['lt50_pct'][gender] = round((avg_section['lt50'][gender] / examined * 100), 1) if examined > 0 else 0
                avg_section['gte50_pct'][gender] = round((avg_section['gte50'][gender] / examined * 100), 1) if examined > 0 else 0
                avg_section['gte75_pct'][gender] = round((avg_section['gte75'][gender] / examined * 100), 1) if examined > 0 else 0
                avg_section['gte85_pct'][gender] = round((avg_section['gte85'][gender] / examined * 100), 1) if examined > 0 else 0
            
            avg_grade['sections'][section_name] = avg_section
        
        # Calculate percentages for grade subtotals
        for gender in ['M', 'F', 'T']:
            examined = avg_grade['subtotals']['examined'][gender]
            avg_grade['subtotals']['lt50_pct'][gender] = round((avg_grade['subtotals']['lt50'][gender] / examined * 100), 1) if examined > 0 else 0
            avg_grade['subtotals']['gte50_pct'][gender] = round((avg_grade['subtotals']['gte50'][gender] / examined * 100), 1) if examined > 0 else 0
            avg_grade['subtotals']['gte75_pct'][gender] = round((avg_grade['subtotals']['gte75'][gender] / examined * 100), 1) if examined > 0 else 0
            avg_grade['subtotals']['gte85_pct'][gender] = round((avg_grade['subtotals']['gte85'][gender] / examined * 100), 1) if examined > 0 else 0
        
        average_data['grade_analysis'].append(avg_grade)
        
        # Accumulate to grand totals
        for metric in ['registered', 'examined', 'lt50', 'gte50', 'gte75', 'gte85']:
            for gender in ['M', 'F']:
                average_data['grand_totals'][metric][gender] += avg_grade['subtotals'][metric][gender]
            average_data['grand_totals'][metric]['T'] = average_data['grand_totals'][metric]['M'] + average_data['grand_totals'][metric]['F']
    
    # Calculate percentages for grand totals
    for gender in ['M', 'F', 'T']:
        examined = average_data['grand_totals']['examined'][gender]
        average_data['grand_totals']['lt50_pct'][gender] = round((average_data['grand_totals']['lt50'][gender] / examined * 100), 1) if examined > 0 else 0
        average_data['grand_totals']['gte50_pct'][gender] = round((average_data['grand_totals']['gte50'][gender] / examined * 100), 1) if examined > 0 else 0
        average_data['grand_totals']['gte75_pct'][gender] = round((average_data['grand_totals']['gte75'][gender] / examined * 100), 1) if examined > 0 else 0
        average_data['grand_totals']['gte85_pct'][gender] = round((average_data['grand_totals']['gte85'][gender] / examined * 100), 1) if examined > 0 else 0
    
    return average_data

def generate_analysis_table_html(grade_analysis, grand_totals):
    """Generate HTML table for analysis results"""
    html = '<div class="table-container"><table class="performance-table"><thead><tr>'
    html += '<th rowspan="2">Grade (1-8)</th>'
    html += '<th colspan="3">Registered</th><th colspan="3">Examined</th>'
    html += '<th colspan="6">Score &lt; 50</th><th colspan="6">Score ≥ 50</th>'
    html += '<th colspan="6">Score ≥ 75</th><th colspan="6">Score ≥ 85</th></tr><tr>'
    html += '<th>M</th><th>F</th><th>T</th><th>M</th><th>F</th><th>T</th>'
    html += '<th>M</th><th>F</th><th>T</th><th>M%</th><th>F%</th><th>T%</th>'
    html += '<th>M</th><th>F</th><th>T</th><th>M%</th><th>F%</th><th>T%</th>'
    html += '<th>M</th><th>F</th><th>T</th><th>M%</th><th>F%</th><th>T%</th>'
    html += '<th>M</th><th>F</th><th>T</th><th>M%</th><th>F%</th><th>T%</th></tr></thead><tbody>'
    
    for grade in grade_analysis:
        gn = grade["grade_name"]
        html += f'<tr class="grade-header"><td colspan="31">Grade {gn}</td></tr>'
        
        for section_name, section in grade["sections"].items():
            sec_letter = get_section_letter(section_name)
            html += f'<tr class="section-row"><td class="subject-col">{gn}-{sec_letter}</td>'
            html += f'<td>{section["registered"]["M"]}</td><td>{section["registered"]["F"]}</td><td>{section["registered"]["T"]}</td>'
            html += f'<td>{section["examined"]["M"]}</td><td>{section["examined"]["F"]}</td><td>{section["examined"]["T"]}</td>'
            html += f'<td>{section["lt50"]["M"]}</td><td>{section["lt50"]["F"]}</td><td>{section["lt50"]["T"]}</td>'
            html += f'<td>{section["lt50_pct"]["M"]}</td><td>{section["lt50_pct"]["F"]}</td><td>{section["lt50_pct"]["T"]}</td>'
            html += f'<td>{section["gte50"]["M"]}</td><td>{section["gte50"]["F"]}</td><td>{section["gte50"]["T"]}</td>'
            html += f'<td>{section["gte50_pct"]["M"]}</td><td>{section["gte50_pct"]["F"]}</td><td>{section["gte50_pct"]["T"]}</td>'
            html += f'<td>{section["gte75"]["M"]}</td><td>{section["gte75"]["F"]}</td><td>{section["gte75"]["T"]}</td>'
            html += f'<td>{section["gte75_pct"]["M"]}</td><td>{section["gte75_pct"]["F"]}</td><td>{section["gte75_pct"]["T"]}</td>'
            html += f'<td>{section["gte85"]["M"]}</td><td>{section["gte85"]["F"]}</td><td>{section["gte85"]["T"]}</td>'
            html += f'<td>{section["gte85_pct"]["M"]}</td><td>{section["gte85_pct"]["F"]}</td><td>{section["gte85_pct"]["T"]}</td></tr>'
        
        subtotals = grade["subtotals"]
        html += f'<tr class="sum-row"><td class="subject-col">Grade {gn} Total</td>'
        html += f'<td>{subtotals["registered"]["M"]}</td><td>{subtotals["registered"]["F"]}</td><td>{subtotals["registered"]["T"]}</td>'
        html += f'<td>{subtotals["examined"]["M"]}</td><td>{subtotals["examined"]["F"]}</td><td>{subtotals["examined"]["T"]}</td>'
        html += f'<td>{subtotals["lt50"]["M"]}</td><td>{subtotals["lt50"]["F"]}</td><td>{subtotals["lt50"]["T"]}</td>'
        html += f'<td>{subtotals["lt50_pct"]["M"]}</td><td>{subtotals["lt50_pct"]["F"]}</td><td>{subtotals["lt50_pct"]["T"]}</td>'
        html += f'<td>{subtotals["gte50"]["M"]}</td><td>{subtotals["gte50"]["F"]}</td><td>{subtotals["gte50"]["T"]}</td>'
        html += f'<td>{subtotals["gte50_pct"]["M"]}</td><td>{subtotals["gte50_pct"]["F"]}</td><td>{subtotals["gte50_pct"]["T"]}</td>'
        html += f'<td>{subtotals["gte75"]["M"]}</td><td>{subtotals["gte75"]["F"]}</td><td>{subtotals["gte75"]["T"]}</td>'
        html += f'<td>{subtotals["gte75_pct"]["M"]}</td><td>{subtotals["gte75_pct"]["F"]}</td><td>{subtotals["gte75_pct"]["T"]}</td>'
        html += f'<td>{subtotals["gte85"]["M"]}</td><td>{subtotals["gte85"]["F"]}</td><td>{subtotals["gte85"]["T"]}</td>'
        html += f'<td>{subtotals["gte85_pct"]["M"]}</td><td>{subtotals["gte85_pct"]["F"]}</td><td>{subtotals["gte85_pct"]["T"]}</td></tr>'
    
    html += f'<tr class="grandtotal-row"><td class="subject-col">GrandSum</td>'
    html += f'<td>{grand_totals["registered"]["M"]}</td><td>{grand_totals["registered"]["F"]}</td><td>{grand_totals["registered"]["T"]}</td>'
    html += f'<td>{grand_totals["examined"]["M"]}</td><td>{grand_totals["examined"]["F"]}</td><td>{grand_totals["examined"]["T"]}</td>'
    html += f'<td>{grand_totals["lt50"]["M"]}</td><td>{grand_totals["lt50"]["F"]}</td><td>{grand_totals["lt50"]["T"]}</td>'
    html += f'<td>{grand_totals["lt50_pct"]["M"]}</td><td>{grand_totals["lt50_pct"]["F"]}</td><td>{grand_totals["lt50_pct"]["T"]}</td>'
    html += f'<td>{grand_totals["gte50"]["M"]}</td><td>{grand_totals["gte50"]["F"]}</td><td>{grand_totals["gte50"]["T"]}</td>'
    html += f'<td>{grand_totals["gte50_pct"]["M"]}</td><td>{grand_totals["gte50_pct"]["F"]}</td><td>{grand_totals["gte50_pct"]["T"]}</td>'
    html += f'<td>{grand_totals["gte75"]["M"]}</td><td>{grand_totals["gte75"]["F"]}</td><td>{grand_totals["gte75"]["T"]}</td>'
    html += f'<td>{grand_totals["gte75_pct"]["M"]}</td><td>{grand_totals["gte75_pct"]["F"]}</td><td>{grand_totals["gte75_pct"]["T"]}</td>'
    html += f'<td>{grand_totals["gte85"]["M"]}</td><td>{grand_totals["gte85"]["F"]}</td><td>{grand_totals["gte85"]["T"]}</td>'
    html += f'<td>{grand_totals["gte85_pct"]["M"]}</td><td>{grand_totals["gte85_pct"]["F"]}</td><td>{grand_totals["gte85_pct"]["T"]}</td></tr>'
    html += '</tbody></table></div>'
    
    return html

@grade_level_analysis_bp.route('/grade_level_analysis')
@login_required
def grade_level_analysis():
    conn = get_db()
    
    # Get filter values
    academic_year_id = request.args.get('year', 0, type=int)
    view = request.args.get('view', 'first')
    
    # Get academic year options
    cursor = conn.cursor(dictionary=True)
    year_options = {}
    years_query = "SELECT ID, year FROM academic_year ORDER BY year DESC"
    cursor.execute(years_query)
    for row in cursor.fetchall():
        year_options[row['ID']] = row['year']
    cursor.close()
    
    semester_data = {'first': None, 'second': None}
    average_data = None
    tables = {'first': '', 'second': '', 'average': ''}
    
    if academic_year_id > 0:
        # Process both semesters
        semester_data['first'] = process_semester_data(conn, academic_year_id, '1')
        semester_data['second'] = process_semester_data(conn, academic_year_id, '2')
        
        # Generate table HTML for each view
        tables['first'] = generate_analysis_table_html(
            semester_data['first']['grade_analysis'], 
            semester_data['first']['grand_totals']
        )
        tables['second'] = generate_analysis_table_html(
            semester_data['second']['grade_analysis'], 
            semester_data['second']['grand_totals']
        )
        
        # Calculate averages
        average_data = calculate_average_data(semester_data['first'], semester_data['second'])
        tables['average'] = generate_analysis_table_html(
            average_data['grade_analysis'], 
            average_data['grand_totals']
        )
    
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, 
                                  year_options=year_options,
                                  academic_year_id=academic_year_id,
                                  view=view,
                                  tables=tables)

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Grade Level Analysis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .performance-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.85em;
        }
        
        .performance-table th, .performance-table td {
            padding: 8px 10px;
            border: 1px solid #ddd;
            text-align: center;
        }
        
        .performance-table th {
            background-color: #2c3e50;
            color: white;
            position: sticky;
            top: 0;
        }
        
        .performance-table tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        .performance-table tr:hover {
            background-color: #e9ecef;
        }
        
        .section-row {
            background-color: #ffffff;
        }
        
        .sum-row {
            background-color: #e9ecef;
            font-weight: bold;
            border-top: 2px solid #dee2e6;
        }
        
        .grandtotal-row {
            background-color: #ced4da;
            font-weight: bold;
        }
        
        .subject-col {
            text-align: left;
            font-weight: bold;
        }
        
        .table-container {
            overflow-x: auto;
            margin-bottom: 20px;
        }
        
        .grade-header {
            background-color: #f1f1f1;
            font-weight: bold;
        }
        
        .semester-header {
            background-color: #e7f4e4;
            padding: 10px;
            margin: 20px 0 10px 0;
            border-left: 4px solid #2ecc71;
            font-weight: bold;
        }
        
        .view-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .view-btn {
            padding: 8px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
        }
        
        .view-btn.active {
            background-color: #2ecc71;
            color: white;
        }
        
        .view-btn:not(.active) {
            background-color: #e9ecef;
            color: #333;
        }
        
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1 class="mb-4">Comprehensive Grade Level Analysis</h1>
        
        <div class="card mb-4">
            <div class="card-body">
                <form method="GET" class="row g-3">
                    <div class="col-md-6">
                        <label for="year" class="form-label">Academic Year</label>
                        <select name="year" id="year" class="form-select" required>
                            <option value="">Select Academic Year</option>
                            {% for id, year in year_options.items() %}
                                <option value="{{ id }}" {% if academic_year_id == id %}selected{% endif %}>
                                    {{ year }}
                                </option>
                            {% endfor %}
                        </select>
                    </div>
                    <input type="hidden" name="view" id="view-input" value="{{ view }}">
                    <div class="col-md-12">
                        <button type="submit" class="btn btn-primary">Generate Report</button>
                        <a href="/director/grade_level_analysis" class="btn btn-secondary">Reset</a>
                    </div>
                </form>
            </div>
        </div>
        
        {% if academic_year_id > 0 %}
        
        <div class="view-buttons">
            <button class="view-btn {% if view == 'first' %}active{% endif %}" 
                    onclick="setView('first')">First Semester</button>
            <button class="view-btn {% if view == 'second' %}active{% endif %}" 
                    onclick="setView('second')">Second Semester</button>
            <button class="view-btn {% if view == 'average' %}active{% endif %}" 
                    onclick="setView('average')">Average</button>
        </div>
        
        <div id="first-semester" class="{% if view != 'first' %}hidden{% endif %}">
            <div class="semester-header">
                <h3>First Semester Results</h3>
            </div>
            {{ tables.first | safe }}
        </div>
        
        <div id="second-semester" class="{% if view != 'second' %}hidden{% endif %}">
            <div class="semester-header">
                <h3>Second Semester Results</h3>
            </div>
            {{ tables.second | safe }}
        </div>
        
        <div id="average-view" class="{% if view != 'average' %}hidden{% endif %}">
            <div class="semester-header">
                <h3>Average of Both Semesters</h3>
            </div>
            {{ tables.average | safe }}
        </div>
        
        {% endif %}
    </div>

    <script>
        function setView(view) {
            document.getElementById('view-input').value = view;
            document.querySelector('form').submit();
        }
    </script>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''