# ==============================================
# insert_student_scores.py
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

@director_insert_student_scores.route('/insert_student_scores', methods=['GET', 'POST'])
@login_required
def insert_student_scores_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            assessment_id = request.form.get('assessment_id')
            score_type = request.form.get('score_type')
            
            for key, value in request.form.items():
                if key.startswith('score_'):
                    student_id = key.split('_')[1]
                    score = value if value else None
                    
                    if score and assessment_id:
                        query = """
                            INSERT INTO student_scores (student_id, assessment_id, score, score_type)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE score = %s, score_type = %s
                        """
                        cursor.execute(query, (student_id, assessment_id, score, score_type, score, score_type))
            
            conn.commit()
            flash('Scores inserted successfully!', 'success')
            return redirect('/director/insert_student_scores')
            
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    # GET request - load assessments
    cursor.execute("""
        SELECT a.ID, a.assessment_name, a.assessment_type, a.max_score,
               g.level as grade_name, s.sec_name as section_name, 
               sub.sub_name as subject_name, ay.year as academic_year
        FROM assessment a
        JOIN grade g ON a.grade_id = g.ID
        JOIN section s ON a.section_id = s.ID
        JOIN subject sub ON a.subject_id = sub.id
        JOIN academic_year ay ON a.academic_year_id = ay.ID
        ORDER BY a.ID DESC
    """)
    assessments = cursor.fetchall()
    
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
            .container-narrow {
                max-width: 1200px;
                margin: 0 auto;
            }
        </style>
    </head>
    <body>
        <div class="container-narrow py-3">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4><i class="fas fa-pen-alt"></i> Insert Student Scores</h4>
                <a href="/director/director_dashboard" class="btn btn-secondary btn-sm">Back to Dashboard</a>
            </div>
            
            <div class="card mb-3">
                <div class="card-body">
                    <form method="GET" id="assessmentForm">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label">Select Assessment</label>
                                <select name="assessment_id" class="form-select" onchange="this.form.submit()">
                                    <option value="">-- Select Assessment --</option>
                                    {% for a in assessments %}
                                        <option value="{{ a.ID }}" {% if request.args.get('assessment_id')|int == a.ID %}selected{% endif %}>
                                            {{ a.assessment_name }} - {{ a.grade_name }} {{ a.section_name }} - {{ a.subject_name }} ({{ a.academic_year }})
                                        </option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            
            {% if request.args.get('assessment_id') %}
                {% set assessment_id = request.args.get('assessment_id')|int %}
                {% set ns = namespace(students=None, assessment=None) %}
                {# We need to fetch data via a sub-request; but for simplicity, we include an AJAX loader #}
                <div id="studentScores" hx-get="/director/get_students_for_scores?assessment_id={{ assessment_id }}" hx-trigger="load"></div>
            {% endif %}
        </div>
        
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script>
            $(document).ready(function() {
                var assessmentId = new URLSearchParams(window.location.search).get('assessment_id');
                if(assessmentId) {
                    $.ajax({
                        url: '/director/get_students_for_scores',
                        type: 'GET',
                        data: {assessment_id: assessmentId},
                        success: function(response) {
                            $('#studentScores').html(response);
                        }
                    });
                }
            });
        </script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    assessments=assessments
    )


@director_insert_student_scores.route('/get_students_for_scores', methods=['GET'])
@login_required
def get_students_for_scores():
    assessment_id = request.args.get('assessment_id')
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT a.grade_id, a.section_id, a.subject_id, a.assessment_name, a.max_score, a.score_type
        FROM assessment a
        WHERE a.ID = %s
    """, (assessment_id,))
    assessment = cursor.fetchone()
    
    cursor.execute("""
        SELECT s.ID as student_id, s.name as student_name, s.student_code,
               COALESCE(ss.score, '') as current_score
        FROM student s
        JOIN enrollment e ON s.ID = e.student_id
        LEFT JOIN student_scores ss ON s.ID = ss.student_id AND ss.assessment_id = %s
        WHERE e.grade_id = %s AND e.section_id = %s AND e.academic_year_id = (
            SELECT academic_year_id FROM assessment WHERE ID = %s
        )
        ORDER BY s.name
    """, (assessment_id, assessment['grade_id'], assessment['section_id'], assessment_id))
    
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">{{ assessment.assessment_name }} - Max Score: {{ assessment.max_score }}</h5>
        </div>
        <div class="card-body">
            <form method="POST" action="/director/insert_student_scores">
                <input type="hidden" name="assessment_id" value="{{ assessment_id }}">
                <input type="hidden" name="score_type" value="{{ assessment.score_type }}">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Student Code</th>
                                <th>Student Name</th>
                                <th>Score</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for student in students %}
                            <tr>
                                <td>{{ student.student_code }}</td>
                                <td>{{ student.student_name }}</td>
                                <td>
                                    <input type="number" step="any" name="score_{{ student.student_id }}" 
                                           value="{{ student.current_score }}" class="form-control" 
                                           style="width: 150px;">
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                <div class="mt-3">
                    <button type="submit" class="btn btn-primary">Save Scores</button>
                </div>
            </form>
        </div>
    </div>
    ''', 
    assessment=assessment, 
    students=students, 
    assessment_id=assessment_id
    )