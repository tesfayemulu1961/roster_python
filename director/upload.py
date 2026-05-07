# ==============================================
# Upload Files - Complete Python Conversion
# Converted from upload.php
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request, url_for
from functools import wraps
import mysql.connector
import os
from datetime import datetime
from werkzeug.utils import secure_filename

director_upload = Blueprint('director_upload', __name__, url_prefix='/director')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        if session.get('user_type') != 'director':
            return redirect('/unauthorized')
        return f(*args, **kwargs)
    return decorated_function

# Configure upload settings
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'gif', 'txt'}

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    return mysql.connector.connect(**db_config)

def get_existing_files_on_disk():
    """Return only files that physically exist on disk."""
    if not os.path.exists(UPLOAD_FOLDER):
        return []
    return [
        f for f in os.listdir(UPLOAD_FOLDER)
        if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))
    ]

@director_upload.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_page():
    message = None
    message_type = None

    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    if request.method == 'POST':
        if 'file' not in request.files:
            message = "No file selected."
            message_type = "danger"
        else:
            file = request.files['file']
            if file.filename == '':
                message = "No file selected."
                message_type = "danger"
            elif not allowed_file(file.filename):
                message = "File type not allowed."
                message_type = "danger"
            else:
                original_filename = file.filename
                filename = secure_filename(original_filename)
                destination = os.path.join(UPLOAD_FOLDER, filename)

                # ── Duplicate check: refuse if file already exists on disk ──
                if os.path.exists(destination):
                    message = f"'{original_filename}' has already been uploaded. Please rename the file or delete the existing one first."
                    message_type = "warning"
                else:
                    file.save(destination)

                    # Save record to DB
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO materials (file_type, file_path, original_filename, upload_date) "
                            "VALUES (%s, %s, %s, %s)",
                            ('Textbook', filename, original_filename, datetime.now())
                        )
                        conn.commit()
                        cursor.close()
                        conn.close()
                    except Exception:
                        pass

                    message = f"'{original_filename}' uploaded successfully!"
                    message_type = "success"

    # ── Only show files that physically exist on disk ──
    uploaded_files = get_existing_files_on_disk()

    return render_template_string(TEMPLATE,
        message=message,
        message_type=message_type,
        uploaded_files=uploaded_files
    )


@director_upload.route('/upload/delete/<filename>', methods=['POST'])
@login_required
def delete_file(filename):
    """Delete a single file from disk and its DB record."""
    safe_name = secure_filename(filename)
    file_path = os.path.join(UPLOAD_FOLDER, safe_name)

    # Remove from disk if it exists
    if os.path.isfile(file_path):
        os.remove(file_path)

    # Remove matching DB record (only one row at a time)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM materials WHERE file_path = %s LIMIT 1",
            (safe_name,)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass

    return redirect(url_for('director_upload.upload_page'))


# ── Template kept separate for readability ──
TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Files - Director Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/core.css">
    <style>
        .upload-container { max-width: 800px; margin: 0 auto; }
        .upload-area {
            border: 2px dashed #dee2e6;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            background: #f8f9fa;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover { border-color: #667eea; background: #f0f0ff; }
        .file-list { margin-top: 20px; }
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        .file-item:hover { background: #f8f9fa; }
    </style>
</head>
<body>
    <div class="container py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h3><i class="fas fa-upload"></i> Upload Files</h3>
            <a href="/director/director_dashboard" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> Back
            </a>
        </div>

        <div class="upload-container">
            {% if message %}
                <div class="alert alert-{{ message_type }} alert-dismissible fade show">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endif %}

            <div class="card">
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                            <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
                            <p class="mb-0">Click or drag file to upload</p>
                            <small class="text-muted">Allowed: PDF, DOC, XLS, PPT, JPG, PNG, TXT</small>
                            <input type="file" id="fileInput" name="file" style="display:none"
                                   onchange="this.form.submit()">
                        </div>
                        <button type="submit" class="btn btn-primary w-100 mt-3">Upload File</button>
                    </form>
                </div>
            </div>

            {% if uploaded_files %}
            <div class="card mt-4">
                <div class="card-header bg-primary text-white">
                    <i class="fas fa-file-alt"></i> Uploaded Files
                </div>
                <div class="card-body file-list p-0">
                    {% for file in uploaded_files %}
                    <div class="file-item px-3">
                        <div>
                            <i class="fas
                                {% if file.endswith('.pdf') %}fa-file-pdf
                                {% elif file.endswith(('.jpg','.jpeg','.png','.gif')) %}fa-file-image
                                {% else %}fa-file-alt{% endif %}
                                me-2"></i>
                            {{ file }}
                        </div>
                        <div class="d-flex gap-2">
                            <a href="/static/uploads/{{ file }}"
                               class="btn btn-sm btn-primary" download>
                                <i class="fas fa-download"></i> Download
                            </a>

                            <!-- Single-file delete: POSTs only this file's name -->
                            <form method="POST"
                                  action="/director/upload/delete/{{ file }}"
                                  onsubmit="return confirm('Delete {{ file }}?')">
                                <button type="submit" class="btn btn-sm btn-danger">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            </form>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/core.js"></script>
</body>
</html>
'''