# ==============================================
# insert_student_scores.py (Fixed for your schema)
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request, flash
from functools import wraps
import mysql.connector

director_insert_student_scores = Blueprint('director_insert_student_scores', __name__, url_prefix='/director')

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

def get_grade_range(grade_id):
    """Determine grade range based on grade level string or int."""
    grade_level = str(grade_id)
    if grade_level in ['KG-1', 'KG-2', 'KG-3']:
        return 'K-G1-KG-3'
    elif grade_level.isdigit():
        g = int(grade_level)
        if 1 <= g <= 6:
            return '1-6'
        elif 7 <= g <= 8:
            return '7-8'
        elif 9 <= g <= 10:
            return '9-10'
    elif '11_Natural' in grade_level or '12_Natural' in grade_level:
        return '11_Natural-12_Natural'
    elif '11_Social' in grade_level or '12_Social' in grade_level:
        return '11_Social-12_Social'
    return 'None'

def get_subjects_by_grade(grade_id, is_blind=False):
    """Return list of required subjects for the grade, considering blind exemption."""
    common = ['Amh', 'Eng']
    grade_range = get_grade_range(grade_id)
    exempt = []
    if is_blind:
        exempt.append('Maths')
        if grade_range == '7-8':
            exempt.extend(['GSc', 'IT', 'CTE'])
        elif grade_range in ['9-10', '11_Natural-12_Natural', '11_Social-12_Social']:
            exempt.append('IT')

    if grade_range == '1-6':
        subjects = ['EnSc', 'Arts', 'HPE', 'Ethics']
        if not is_blind:
            subjects.append('Maths')
    elif grade_range == '7-8':
        subjects = ['SSc', 'Ctzp', 'Arts', 'HPE']
        if not is_blind:
            subjects.extend(['Maths', 'GSc', 'IT', 'CTE'])
    elif grade_range == '9-10':
        subjects = ['Bio', 'Chem', 'Phy', 'Hist', 'Geo', 'HPE', 'Ctzp']
        if not is_blind:
            subjects.extend(['Maths', 'IT'])
    elif grade_range in ['11_Natural-12_Natural', '11_Social-12_Social']:
        if grade_range == '11_Natural-12_Natural':
            subjects = ['Bio', 'Chem', 'Phy', 'Agri', 'Voc']
        else:
            subjects = ['Hist', 'Geo', 'Econ', 'Voc']
        if not is_blind:
            subjects.extend(['Maths', 'IT'])
    else:
        subjects = []

    return [s for s in common + subjects if s not in exempt]

@director_insert_student_scores.route('/insert_student_scores', methods=['GET', 'POST'])
@login_required
def insert_student_scores_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Get all possible subject columns from student_scores table (excluding fixed ones)
    cursor.execute("DESCRIBE student_scores")
    columns = cursor.fetchall()
    all_subjects = []
    fixed_columns = ['ID', 'student_RN', 'academic_year_id', 'grade_id', 'section_id', 'teacher_id', 'semester']
    for col in columns:
        if col['Field'] not in fixed_columns:
            all_subjects.append(col['Field'])

    # Load dropdown options
    cursor.execute("SELECT ID, year FROM academic_year ORDER BY year DESC")
    academic_years = cursor.fetchall()

    cursor.execute("SELECT ID, level FROM grade ORDER BY ID")
    grades = cursor.fetchall()

    # Handle GET filters
    academic_year_id = request.args.get('academic_year', type=int)
    grade_id = request.args.get('grade', type=int)
    section_id = request.args.get('section', type=int)

    sections = []
    teachers = []
    students = []

    if academic_year_id and grade_id:
        # Get sections for the selected grade
        cursor.execute("SELECT ID, sec_name FROM section WHERE grade_id = %s ORDER BY sec_name", (grade_id,))
        sections = cursor.fetchall()

    if academic_year_id and grade_id and section_id:
        # Get teachers assigned to this grade & section (room teachers)
        cursor.execute("""
            SELECT DISTINCT t.ID, t.t_id, t.name
            FROM teacher t
            JOIN teacher_assignment ta ON t.ID = ta.teacher_id
            WHERE ta.grade_id = %s AND ta.section_id = %s AND ta.is_room_teacher = 1
        """, (grade_id, section_id))
        teachers = cursor.fetchall()

        # Get students enrolled
        cursor.execute("""
            SELECT s.RN, s.studid, s.name as fullname, s.is_blind
            FROM student s
            JOIN enrollment e ON s.ID = e.student_id
            WHERE e.academic_year_id = %s AND e.grade_id = %s AND e.section_id = %s
            ORDER BY s.name
        """, (academic_year_id, grade_id, section_id))
        students = cursor.fetchall()

    # Handle POST submission
    if request.method == 'POST':
        student_rn = request.form.get('student_RN')
        academic_year_id_post = request.form.get('academic_year_id', type=int)
        grade_id_post = request.form.get('grade_id', type=int)
        section_id_post = request.form.get('section_id', type=int)
        teacher_id = request.form.get('teacher_id', type=int)
        semester = request.form.get('semester')
        is_blind = request.form.get('is_blind') == 'on'

        # Get student info to check blind status and studid
        cursor.execute("SELECT studid, is_blind FROM student WHERE RN = %s", (student_rn,))
        student_info = cursor.fetchone()
        if not student_info:
            flash('Student not found!', 'danger')
            return redirect(request.url)

        studid = student_info['studid']
        is_blind_db = bool(student_info['is_blind'])
        is_blind = is_blind or is_blind_db

        # Determine required subjects
        required_subjects = get_subjects_by_grade(grade_id_post, is_blind)

        # Validate required subjects
        scores = {}
        missing = []
        for subject in required_subjects:
            score_str = request.form.get(subject, '')
            if score_str == '':
                missing.append(subject)
            else:
                try:
                    score = float(score_str)
                    if score < 0 or score > 100:
                        missing.append(f"{subject} (out of range)")
                    else:
                        scores[subject] = score
                except ValueError:
                    missing.append(f"{subject} (invalid number)")

        # Also collect optional subjects (if present)
        for subject in all_subjects:
            if subject not in scores and subject in request.form and request.form[subject] != '':
                try:
                    scores[subject] = float(request.form[subject])
                except:
                    pass

        if missing:
            flash(f'Missing or invalid required subjects: {", ".join(missing)}', 'danger')
        else:
            # Check if scores already exist for this student, academic year, semester
            cursor.execute("""
                SELECT ID FROM student_scores 
                WHERE student_RN = %s AND academic_year_id = %s AND semester = %s
            """, (student_rn, academic_year_id_post, semester))
            if cursor.fetchone():
                flash('Scores already exist for this student in the selected semester!', 'danger')
            else:
                # Build dynamic INSERT query
                columns = ['student_RN', 'academic_year_id', 'grade_id', 'section_id', 'teacher_id', 'semester']
                placeholders = ['%s'] * len(columns)
                values = [student_rn, academic_year_id_post, grade_id_post, section_id_post, teacher_id, semester]

                for subject in all_subjects:
                    if subject in scores:
                        columns.append(subject)
                        placeholders.append('%s')
                        values.append(scores[subject])
                    else:
                        # For missing subjects, we need to insert NULL (but we must still add column with NULL)
                        columns.append(subject)
                        placeholders.append('NULL')  # we'll handle dynamically
                        # We'll build the query with conditional placeholders later
                # Rebuild query with proper placeholders (using list comprehension)
                # Simpler: build two lists: ones with values and ones without
                insert_columns = []
                insert_placeholders = []
                insert_values = []
                for subject in all_subjects:
                    insert_columns.append(subject)
                    if subject in scores:
                        insert_placeholders.append('%s')
                        insert_values.append(scores[subject])
                    else:
                        insert_placeholders.append('NULL')
                # Now final query
                full_columns = columns + insert_columns
                full_placeholders = placeholders + insert_placeholders
                full_values = values + insert_values

                query = f"INSERT INTO student_scores ({','.join(full_columns)}) VALUES ({','.join(full_placeholders)})"
                # Replace 'NULL' strings in placeholders with actual NULL in SQL; but we already set placeholders to 'NULL'
                # However, placeholders list contains both '%s' and 'NULL'. For '%s' we need to pass values; for 'NULL' we don't.
                # We need to build the query dynamically with conditional placeholders.
                # Let's do it properly:
                final_columns = ['student_RN', 'academic_year_id', 'grade_id', 'section_id', 'teacher_id', 'semester']
                final_values = [student_rn, academic_year_id_post, grade_id_post, section_id_post, teacher_id, semester]
                final_placeholders = ['%s'] * 6

                for subject in all_subjects:
                    final_columns.append(subject)
                    if subject in scores:
                        final_placeholders.append('%s')
                        final_values.append(scores[subject])
                    else:
                        final_placeholders.append('NULL')

                insert_sql = f"INSERT INTO student_scores ({','.join(final_columns)}) VALUES ({','.join(final_placeholders)})"
                try:
                    cursor.execute(insert_sql, final_values)
                    conn.commit()
                    flash('Scores added successfully!', 'success')
                    return redirect(request.url)
                except Exception as e:
                    conn.rollback()
                    flash(f'Database error: {str(e)}', 'danger')

    cursor.close()
    conn.close()

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Insert Student Scores</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        <style>
            .container-narrow { max-width: 1200px; margin: 0 auto; }
            .score-input { width: 70px; text-align: center; }
            .subject-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
            .subject-row label { width: 80px; font-weight: 500; }
            .not-applicable { font-size: 0.75rem; color: #6c757d; margin-left: 8px; }
        </style>
    </head>
    <body>
        <div class="container-narrow py-3">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4><i class="fas fa-plus-circle"></i> Add Student Scores</h4>
                <a href="/director/director_dashboard" class="btn btn-secondary btn-sm">Back</a>
            </div>

            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'danger' else 'success' }} alert-dismissible fade show" role="alert">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <!-- Filter Form -->
            <form method="GET" class="card mb-3">
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-4">
                            <label class="form-label">Academic Year</label>
                            <select name="academic_year" class="form-select" onchange="this.form.submit()">
                                <option value="">-- Select --</option>
                                {% for ay in academic_years %}
                                    <option value="{{ ay.ID }}" {% if academic_year_id == ay.ID %}selected{% endif %}>{{ ay.year }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Grade</label>
                            <select name="grade" class="form-select" onchange="this.form.submit()">
                                <option value="">-- Select --</option>
                                {% for g in grades %}
                                    <option value="{{ g.ID }}" {% if grade_id == g.ID %}selected{% endif %}>{{ g.level }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Section</label>
                            <select name="section" class="form-select" onchange="this.form.submit()">
                                <option value="">-- Select --</option>
                                {% for s in sections %}
                                    <option value="{{ s.ID }}" {% if section_id == s.ID %}selected{% endif %}>{{ s.sec_name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                </div>
            </form>

            {% if students %}
            <form method="POST">
                <input type="hidden" name="academic_year_id" value="{{ academic_year_id }}">
                <input type="hidden" name="grade_id" value="{{ grade_id }}">
                <input type="hidden" name="section_id" value="{{ section_id }}">

                <div class="card mb-3">
                    <div class="card-body">
                        <div class="row g-3">
                            <div class="col-md-4">
                                <label class="form-label">Student</label>
                                <select name="student_RN" class="form-select" required>
                                    <option value="">-- Select --</option>
                                    {% for s in students %}
                                        <option value="{{ s.RN }}" {% if request.form.get('student_RN')|string == s.RN|string %}selected{% endif %}>
                                            {{ s.fullname }} ({{ s.studid }})
                                        </option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Teacher</label>
                                <select name="teacher_id" class="form-select" required>
                                    <option value="">-- Select --</option>
                                    {% for t in teachers %}
                                        <option value="{{ t.ID }}" {% if request.form.get('teacher_id')|int == t.ID %}selected{% endif %}>
                                            {{ t.name }} ({{ t.t_id }})
                                        </option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="col-md-2">
                                <label class="form-label">Semester</label>
                                <select name="semester" class="form-select" required>
                                    <option value="1" {% if request.form.get('semester') == '1' %}selected{% endif %}>Semester 1</option>
                                    <option value="2" {% if request.form.get('semester') == '2' %}selected{% endif %}>Semester 2</option>
                                </select>
                            </div>
                            <div class="col-md-2 d-flex align-items-end">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="is_blind" id="is_blind" {% if request.form.get('is_blind') %}checked{% endif %}>
                                    <label class="form-check-label" for="is_blind">
                                        <i class="fas fa-eye-slash"></i> Blind Student
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <strong>Subject Scores</strong>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            {% set cols = all_subjects|length // 3 + 1 %}
                            {% for i in range(0, all_subjects|length, cols) %}
                            <div class="col-md-4">
                                {% for subject in all_subjects[i:i+cols] %}
                                <div class="subject-row">
                                    <label>{{ subject }}:</label>
                                    <input type="number" step="0.1" name="{{ subject }}" class="form-control score-input"
                                           min="0" max="100" value="{{ request.form.get(subject, '') }}">
                                    {% if subject in required_list %}
                                        <span class="text-danger small">*</span>
                                    {% else %}
                                        <span class="not-applicable">(Opt)</span>
                                    {% endif %}
                                </div>
                                {% endfor %}
                            </div>
                            {% endfor %}
                        </div>
                        <div class="mt-3 text-center">
                            <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Save Scores</button>
                            <button type="reset" class="btn btn-secondary">Reset</button>
                        </div>
                    </div>
                </div>
            </form>
            {% else %}
                {% if academic_year_id and grade_id and section_id %}
                <div class="alert alert-info">No students found for the selected criteria.</div>
                {% endif %}
            {% endif %}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Optional: dynamic teacher loading could be added, but teachers are fetched on GET.
        </script>
    </body>
    </html>
    ''',
    academic_years=academic_years,
    grades=grades,
    sections=sections,
    teachers=teachers,
    students=students,
    academic_year_id=academic_year_id,
    grade_id=grade_id,
    section_id=section_id,
    all_subjects=all_subjects,
    required_list=get_subjects_by_grade(grade_id or 0, False)  # placeholder
    )