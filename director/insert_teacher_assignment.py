# ==============================================
# Insert Teacher Assignment - Complete Python Conversion
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import json

director_teacher_assignment = Blueprint('director_teacher_assignment', __name__, url_prefix='/director')

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

@director_teacher_assignment.route('/insert_teacher_assignment', methods=['GET', 'POST'])
@login_required
def insert_teacher_assignment_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    message = None
    message_type = None

    # Dropdown data
    cursor.execute("SELECT ID, name FROM teacher WHERE status = 'active' ORDER BY name")
    teachers = cursor.fetchall()

    cursor.execute("SELECT ID, level FROM grade ORDER BY ID")
    grades = cursor.fetchall()

    # Load ALL sections and subjects with grade_id so JS can filter them
    cursor.execute("SELECT ID, sec_name, grade_id FROM section ORDER BY sec_name")
    sections_raw = cursor.fetchall()

    cursor.execute("SELECT ID, sub_name, grade_id FROM subject ORDER BY sub_name")
    subjects_raw = cursor.fetchall()

    cursor.execute("SELECT ID, year FROM academic_year ORDER BY year DESC")
    academic_years = cursor.fetchall()

    # Group by grade_id for JS lookup
    sections_by_grade = {}
    for s in sections_raw:
        gid = str(s['grade_id'])
        sections_by_grade.setdefault(gid, []).append({'id': s['ID'], 'name': s['sec_name']})

    subjects_by_grade = {}
    for s in subjects_raw:
        gid = str(s['grade_id'])
        subjects_by_grade.setdefault(gid, []).append({'id': s['ID'], 'name': s['sub_name']})

    # POST handler
    if request.method == 'POST':
        teacher_id       = request.form.get('teacher_id', '').strip()
        grade_id         = request.form.get('grade_id', '').strip()
        section_id       = request.form.get('section_id', '').strip()
        subject_id       = request.form.get('subject_id', '').strip()
        academic_year_id = request.form.get('academic_year_id', '').strip()
        assignment_type  = request.form.get('assignment_type', '').strip()

        is_room_teacher    = 1 if assignment_type == 'room'    else 0
        is_subject_teacher = 1 if assignment_type == 'subject' else 0

        if not teacher_id or not grade_id or not academic_year_id:
            message      = "Teacher, Grade and Academic Year are required."
            message_type = "danger"
        else:
            try:
                # Duplicate check
                cursor.execute("""
                    SELECT ID FROM teacher_assignment
                    WHERE teacher_id = %s
                      AND grade_id   = %s
                      AND COALESCE(section_id, 0) = COALESCE(%s, 0)
                      AND COALESCE(subject_id, 0) = COALESCE(%s, 0)
                      AND academic_year_id = %s
                    LIMIT 1
                """, (
                    teacher_id, grade_id,
                    section_id or None,
                    subject_id or None,
                    academic_year_id
                ))
                existing = cursor.fetchone()

                if existing:
                    message      = "This assignment already exists. Please check existing assignments."
                    message_type = "warning"
                else:
                    cursor.execute("""
                        INSERT INTO teacher_assignment
                            (teacher_id, grade_id, section_id, subject_id,
                             academic_year_id, is_room_teacher, is_subject_teacher)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        teacher_id, grade_id,
                        section_id or None,
                        subject_id or None,
                        academic_year_id,
                        is_room_teacher, is_subject_teacher
                    ))
                    conn.commit()
                    message      = "Teacher assigned successfully!"
                    message_type = "success"

            except Exception as e:
                message      = f"Database error: {e}"
                message_type = "danger"

    cursor.close()
    conn.close()

    return render_template_string(TEMPLATE,
        teachers=teachers,
        grades=grades,
        academic_years=academic_years,
        sections_json=json.dumps(sections_by_grade),
        subjects_json=json.dumps(subjects_by_grade),
        message=message,
        message_type=message_type,
    )


TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Assign Teacher</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/core.css">
    <style>
        .form-container {
            max-width: 700px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            padding: 28px;
            box-shadow: 0 2px 12px rgba(0,0,0,.07);
        }
        .form-label { font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 4px; }
        .form-select { font-size: 13.5px; }
        .form-select:disabled { background: #f9fafb; color: #9ca3af; }
        .required-star { color: #dc2626; }
        .hint { font-size: 11.5px; color: #9ca3af; margin-top: 3px; }
    </style>
</head>
<body>
<div class="container py-4">
    <div class="form-container">
        <div class="d-flex align-items-center justify-content-between mb-4">
            <h5 class="mb-0"><i class="fas fa-user-plus text-primary me-2"></i>Assign Teacher</h5>
            <a href="/director/director_dashboard" class="btn btn-outline-secondary btn-sm">
                <i class="fas fa-arrow-left me-1"></i>Back
            </a>
        </div>

        {% if message %}
        <div class="alert alert-{{ message_type }} alert-dismissible fade show py-2" role="alert">
            <i class="fas fa-{{ 'check-circle' if message_type == 'success' else 'exclamation-triangle' }} me-2"></i>
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endif %}

        <form method="POST" id="assignForm">
            <div class="row g-3">

                <div class="col-md-6">
                    <label class="form-label">Teacher <span class="required-star">*</span></label>
                    <select name="teacher_id" class="form-select" required>
                        <option value="">— Select Teacher —</option>
                        {% for t in teachers %}
                            <option value="{{ t.ID }}">{{ t.name }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="col-md-6">
                    <label class="form-label">Assignment Type <span class="required-star">*</span></label>
                    <select name="assignment_type" class="form-select" required>
                        <option value="room">Room Teacher</option>
                        <option value="subject">Subject Teacher</option>
                    </select>
                </div>

                <div class="col-md-6">
                    <label class="form-label">Grade <span class="required-star">*</span></label>
                    <select name="grade_id" id="gradeSelect" class="form-select" required>
                        <option value="">— Select Grade —</option>
                        {% for g in grades %}
                            <option value="{{ g.ID }}">{{ g.level }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="col-md-6">
                    <label class="form-label">Academic Year <span class="required-star">*</span></label>
                    <select name="academic_year_id" class="form-select" required>
                        <option value="">— Select Year —</option>
                        {% for y in academic_years %}
                            <option value="{{ y.ID }}">{{ y.year }}</option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Section: locked until grade chosen -->
                <div class="col-md-6">
                    <label class="form-label">Section</label>
                    <select name="section_id" id="sectionSelect" class="form-select" disabled>
                        <option value="">— Select Grade first —</option>
                    </select>
                    <div class="hint"><i class="fas fa-info-circle me-1"></i>Choose a grade to load sections</div>
                </div>

                <!-- Subject: locked until grade chosen -->
                <div class="col-md-6">
                    <label class="form-label">Subject</label>
                    <select name="subject_id" id="subjectSelect" class="form-select" disabled>
                        <option value="">— Select Grade first —</option>
                    </select>
                    <div class="hint"><i class="fas fa-info-circle me-1"></i>Choose a grade to load subjects</div>
                </div>

            </div>

            <button type="submit" class="btn btn-primary w-100 mt-4">
                <i class="fas fa-save me-2"></i>Assign Teacher
            </button>
        </form>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="/static/js/core.js"></script>
<script>
const SECTIONS_BY_GRADE = {{ sections_json | safe }};
const SUBJECTS_BY_GRADE = {{ subjects_json | safe }};

const gradeSelect   = document.getElementById('gradeSelect');
const sectionSelect = document.getElementById('sectionSelect');
const subjectSelect = document.getElementById('subjectSelect');

function populateSelect(selectEl, items, placeholder) {
    selectEl.innerHTML = '';
    const blank = document.createElement('option');
    blank.value = '';
    blank.textContent = placeholder;
    selectEl.appendChild(blank);

    if (items && items.length > 0) {
        items.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.id;
            opt.textContent = item.name;
            selectEl.appendChild(opt);
        });
        selectEl.disabled = false;
    } else {
        const none = document.createElement('option');
        none.value = '';
        none.textContent = '— None available for this grade —';
        selectEl.appendChild(none);
        selectEl.disabled = true;
    }
}

gradeSelect.addEventListener('change', function () {
    const gid = this.value;
    if (!gid) {
        sectionSelect.innerHTML = '<option value="">— Select Grade first —</option>';
        sectionSelect.disabled = true;
        subjectSelect.innerHTML = '<option value="">— Select Grade first —</option>';
        subjectSelect.disabled = true;
        return;
    }
    populateSelect(sectionSelect, SECTIONS_BY_GRADE[gid] || [], '— Select Section —');
    populateSelect(subjectSelect, SUBJECTS_BY_GRADE[gid] || [], '— Select Subject —');
});
</script>
</body>
</html>
'''