# ==============================================
# excel_import.py
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request, flash
from functools import wraps
import mysql.connector
import pandas as pd
import os
from werkzeug.utils import secure_filename

director_excel_import = Blueprint('director_excel_import', __name__, url_prefix='/director')

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

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@director_excel_import.route('/excel_import', methods=['GET', 'POST'])
@login_required
def excel_import_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            import_type = request.form.get('import_type')
            table_name = request.form.get('table_name')
            
            if 'file' not in request.files:
                flash('No file uploaded', 'danger')
                return redirect(request.url)
            
            file = request.files['file']
            
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Read Excel/CSV file
                if filename.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)
                
                # Import data based on table name
                success_count = 0
                error_count = 0
                
                for _, row in df.iterrows():
                    try:
                        if table_name == 'student':
                            query = """
                                INSERT INTO student (name, student_code, phone, email, address)
                                VALUES (%s, %s, %s, %s, %s)
                            """
                            cursor.execute(query, (
                                row.get('name'), row.get('student_code'),
                                row.get('phone'), row.get('email'), row.get('address')
                            ))
                            
                        elif table_name == 'teacher':
                            query = """
                                INSERT INTO teacher (name, t_id, phone, email, qualification)
                                VALUES (%s, %s, %s, %s, %s)
                            """
                            cursor.execute(query, (
                                row.get('name'), row.get('t_id'),
                                row.get('phone'), row.get('email'), row.get('qualification')
                            ))
                            
                        elif table_name == 'enrollment':
                            query = """
                                INSERT INTO enrollment (student_id, grade_id, section_id, academic_year_id)
                                VALUES (%s, %s, %s, %s)
                            """
                            cursor.execute(query, (
                                row.get('student_id'), row.get('grade_id'),
                                row.get('section_id'), row.get('academic_year_id')
                            ))
                        
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        continue
                
                conn.commit()
                flash(f'Import completed! {success_count} records imported, {error_count} errors.', 'success')
                
                # Clean up uploaded file
                os.remove(filepath)
                
            else:
                flash('Invalid file type. Please upload Excel or CSV file.', 'danger')
                
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Excel Import</title>
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
                <h4><i class="fas fa-file-excel"></i> Import Data from Excel</h4>
                <a href="/director/director_dashboard" class="btn btn-secondary btn-sm">Back to Dashboard</a>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="mb-3">
                            <label class="form-label">Select Table to Import</label>
                            <select name="table_name" class="form-select" required>
                                <option value="">-- Select Table --</option>
                                <option value="student">Students</option>
                                <option value="teacher">Teachers</option>
                                <option value="enrollment">Enrollments</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Import Type</label>
                            <select name="import_type" class="form-select" required>
                                <option value="insert">Insert New Records</option>
                                <option value="update">Update Existing Records</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Upload Excel/CSV File</label>
                            <input type="file" name="file" class="form-control" accept=".xlsx,.xls,.csv" required>
                            <small class="text-muted">Supported formats: .xlsx, .xls, .csv</small>
                        </div>
                        
                        <div class="mt-3">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-upload"></i> Import Data
                            </button>
                            <button type="reset" class="btn btn-secondary">Reset</button>
                        </div>
                    </form>
                    
                    <hr class="my-4">
                    
                    <h6 class="mb-3">Download Templates</h6>
                    <div class="list-group">
                        <a href="#" class="list-group-item list-group-item-action">
                            <i class="fas fa-download"></i> Student Import Template
                        </a>
                        <a href="#" class="list-group-item list-group-item-action">
                            <i class="fas fa-download"></i> Teacher Import Template
                        </a>
                        <a href="#" class="list-group-item list-group-item-action">
                            <i class="fas fa-download"></i> Enrollment Import Template
                        </a>
                    </div>
                    
                    <div class="alert alert-info mt-3 small">
                        <i class="fas fa-info-circle"></i> Instructions:
                        <ul class="mb-0 mt-2">
                            <li>Prepare your Excel file with column names matching the database fields</li>
                            <li>Required columns for Students: name, student_code, phone, email, address</li>
                            <li>Required columns for Teachers: name, t_id, phone, email, qualification</li>
                            <li>Required columns for Enrollments: student_id, grade_id, section_id, academic_year_id</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''')