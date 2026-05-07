# ==============================================
# insert_assessment.py
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request, flash
from functools import wraps
import mysql.connector

director_insert_assessment = Blueprint('director_insert_assessment', __name__, url_prefix='/director')

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

@director_insert_assessment.route('/insert_assessment', methods=['GET', 'POST'])
@login_required
def insert_assessment_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            assessment_name = request.form.get('assessment_name')
            assessment_type = request.form.get('assessment_type')
            grade_id = request.form.get('grade_id')
            section_id = request.form.get('section_id')
            subject_id = request.form.get('subject_id')
            academic_year_id = request.form.get('academic_year_id')
            max_score = request.form.get('max_score', 100)
            weight = request.form.get('weight', 1)
            date_taken = request.form.get('date_taken')
            
            query = """
                INSERT INTO assessment (assessment_name, assessment_type, grade_id, section_id, 
                                       subject_id, academic_year_id, max_score, weight, date_taken)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (assessment_name, assessment_type, grade_id, section_id, 
                                  subject_id, academic_year_id, max_score, weight, date_taken))
            conn.commit()
            flash('Assessment added successfully!', 'success')
            return redirect('/director/insert_assessment')
            
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    # GET request - load form data
    cursor.execute("SELECT ID, year FROM academic_year ORDER BY year DESC")
    academic_years = cursor.fetchall()
    
    cursor.execute("SELECT ID, level FROM grade ORDER BY ID")
    grades = cursor.fetchall()
    
    cursor.execute("SELECT ID, sub_name FROM subject ORDER BY sub_name")
    subjects = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Insert Assessment</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        <style>
            .container-narrow {
                max-width: 800px;
                margin: 0 auto;
            }
        </style>
    </head>
    <body>
        <div class="container-narrow py-3">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4><i class="fas fa-plus-circle"></i> Add New Assessment</h4>
                <a href="/director/director_dashboard" class="btn btn-secondary btn-sm">Back to Dashboard</a>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Assessment Name</label>
                            <input type="text" name="assessment_name" class="form-control" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Assessment Type</label>
                            <select name="assessment_type" class="form-select" required>
                                <option value="quiz">Quiz</option>
                                <option value="midterm">Midterm Exam</option>
                                <option value="final">Final Exam</option>
                                <option value="assignment">Assignment</option>
                                <option value="project">Project</option>
                            </select>
                        </div>
                        
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <label class="form-label">Grade</label>
                                <select name="grade_id" id="grade_id" class="form-select" required>
                                    <option value="">Select Grade</option>
                                    {% for g in grades %}
                                        <option value="{{ g.ID }}">{{ g.level }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Section</label>
                                <select name="section_id" id="section_id" class="form-select" required>
                                    <option value="">Select Grade First</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <label class="form-label">Subject</label>
                                <select name="subject_id" class="form-select" required>
                                    <option value="">Select Subject</option>
                                    {% for sub in subjects %}
                                        <option value="{{ sub.ID }}">{{ sub.sub_name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Academic Year</label>
                                <select name="academic_year_id" class="form-select" required>
                                    {% for ay in academic_years %}
                                        <option value="{{ ay.ID }}">{{ ay.year }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <label class="form-label">Max Score</label>
                                <input type="number" name="max_score" class="form-control" value="100" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Weight</label>
                                <input type="number" name="weight" class="form-control" value="1" step="0.1">
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Date Taken</label>
                            <input type="date" name="date_taken" class="form-control">
                        </div>
                        
                        <div class="mt-3">
                            <button type="submit" class="btn btn-primary">Save Assessment</button>
                            <button type="reset" class="btn btn-secondary">Reset</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script>
            $('#grade_id').change(function() {
                var gradeId = $(this).val();
                if(gradeId) {
                    $.ajax({
                        url: '/director/get_sections_by_grade',
                        type: 'GET',
                        data: {grade_id: gradeId},
                        success: function(data) {
                            $('#section_id').html(data);
                        }
                    });
                } else {
                    $('#section_id').html('<option value="">Select Grade First</option>');
                }
            });
        </script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    academic_years=academic_years,
    grades=grades,
    subjects=subjects
    )

# AJAX route for sections
@director_insert_assessment.route('/get_sections_by_grade', methods=['GET'])
@login_required
def get_sections_by_grade():
    grade_id = request.args.get('grade_id')
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT ID, sec_name FROM section WHERE grade_id = %s ORDER BY sec_name", (grade_id,))
    sections = cursor.fetchall()
    cursor.close()
    conn.close()
    
    html = '<option value="">Select Section</option>'
    for section in sections:
        html += f'<option value="{section["ID"]}">{section["sec_name"]}</option>'
    
    return html