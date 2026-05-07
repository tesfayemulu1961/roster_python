# ==============================================
# Materials (Download Files) - With Pagination
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, send_from_directory, request
from functools import wraps
from werkzeug.utils import secure_filename
import mysql.connector
import os
import math
from datetime import datetime

director_materials = Blueprint('director_materials', __name__, url_prefix='/director')

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

UPLOAD_FOLDER = 'static/uploads'

# Create upload folder if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@director_materials.route('/materials')
@login_required
def materials_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    file_type = request.args.get('type', '', type=str)
    
    offset = (page - 1) * per_page
    
    try:
        cursor.execute("SELECT ID as id, grade_id, subject_id, file_type, file_path, original_filename, upload_date FROM materials ORDER BY ID DESC")
        materials = cursor.fetchall()

        # Discover actual column names so we don't guess wrong
        cursor.execute("SHOW COLUMNS FROM materials")
        db_columns = {row['Field'].lower(): row['Field'] for row in cursor.fetchall()}
    except:
        materials = []
        db_columns = {}

    cursor.close()
    conn.close()

    def _pick(row, *candidates, default=None):
        """Return the first matching value from a dict, trying multiple candidate keys."""
        for key in candidates:
            # try exact, lowercase, and discovered column mapping
            for k in (key, key.lower(), db_columns.get(key.lower(), '')):
                if k and k in row and row[k] not in (None, '', 0):
                    return row[k]
        return default

    # Get files from uploads folder with file info
    uploaded_files = []
    if os.path.exists(UPLOAD_FOLDER):
        for f in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, f)
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                file_ext = f.split('.')[-1].upper() if '.' in f else 'FILE'
                uploaded_files.append({
                    'name': f,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'extension': file_ext,
                    'source': 'folder',
                    'path': f
                })

    # Build a quick lookup: lowercase filename -> size from disk
    disk_size_lookup = {f['name'].lower(): f['size'] for f in uploaded_files}

    # Combine materials from DB and files
    all_materials = []
    for m in materials:
        # Display name: use original_filename, fall back to file_path
        name = m.get('original_filename') or m.get('file_path') or 'Untitled'

        file_path_value = m.get('file_path', '') or ''

        # Build the disk path the same way upload.py saved it:
        # secure_filename() was applied at upload time, so we must apply it here too
        # when resolving which file to look for on disk.
        sanitized_name = secure_filename(os.path.basename(file_path_value)) if file_path_value else ''
        if not sanitized_name:
            sanitized_name = secure_filename(name)

        disk_path = os.path.join(UPLOAD_FOLDER, sanitized_name) if sanitized_name else ''

        # Hard skip: do NOT show this row if the file is not physically on disk
        if not disk_path or not os.path.isfile(disk_path):
            continue

        # Size from disk (file confirmed to exist)
        try:
            size = os.stat(disk_path).st_size
        except Exception:
            size = 0

        # Extension: derive from original_filename or file_path
        ext_source = name if '.' in name else file_path_value
        file_ext = ext_source.rsplit('.', 1)[-1].upper() if '.' in ext_source else 'FILE'

        # Date
        modified = m.get('upload_date', 'N/A')
        if hasattr(modified, 'strftime'):
            modified = modified.strftime('%Y-%m-%d %H:%M:%S')

        all_materials.append({
            'name': name,
            'sanitized_name': sanitized_name,
            'size': size,
            'modified': str(modified),
            'extension': file_ext,
            'source': 'database',
            'id': m.get('id') if m.get('id') is not None else m.get('ID')
        })
    
    # Build set of filenames already tracked in DB to avoid duplicates
    db_filenames = set()
    for m in materials:
        fp = m.get('file_path') or m.get('file_path', '')
        if fp:
            db_filenames.add(os.path.basename(fp).lower())

    for f in uploaded_files:
        if f['name'].lower() not in db_filenames:
            all_materials.append({
                'name': f['name'],
                'size': f['size'],
                'modified': f['modified'],
                'extension': f['extension'],
                'source': 'folder',
                'path': f['name']
            })
    
    # Apply search filter
    if search:
        all_materials = [m for m in all_materials if search.lower() in m['name'].lower()]
    
    # Apply file type filter
    if file_type and file_type != 'all':
        all_materials = [m for m in all_materials if m['extension'].lower() == file_type.lower() or 
                         (file_type == 'image' and m['extension'].lower() in ['jpg', 'jpeg', 'png', 'gif'])]
    
    # Sort by modified date (newest first)
    all_materials.sort(key=lambda x: x['modified'], reverse=True)
    
    # Calculate pagination
    total_count = len(all_materials)
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    
    # Slice for current page
    start_idx = offset
    end_idx = min(start_idx + per_page, total_count)
    paginated_materials = all_materials[start_idx:end_idx]
    
    # Calculate showing range
    start_show = start_idx + 1 if total_count > 0 else 0
    end_show = end_idx
    
    # Generate page range for display
    max_visible = 5
    half = max_visible // 2
    start_page = max(1, page - half)
    end_page = min(total_pages, start_page + max_visible - 1)
    
    if end_page - start_page + 1 < max_visible:
        start_page = max(1, end_page - max_visible + 1)
    
    page_range = range(start_page, end_page + 1)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Materials - Download Files</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        <style>
            .table-container {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
            .file-icon {
                font-size: 1.2rem;
                margin-right: 8px;
            }
            .file-pdf { color: #dc3545; }
            .file-doc { color: #2c7be5; }
            .file-xls { color: #28a745; }
            .file-ppt { color: #fd7e14; }
            .file-img { color: #6f42c1; }
            .file-txt { color: #6c757d; }
            .file-default { color: #667eea; }
            .pagination .page-link {
                padding: 6px 12px;
                font-size: 13px;
            }
            .pagination .active .page-link {
                background-color: #667eea;
                border-color: #667eea;
            }
            .btn-download {
                padding: 4px 12px;
                font-size: 12px;
            }
            .table th {
                background-color: #f8f9fa;
                font-weight: 600;
            }
            .filter-active {
                background-color: #667eea !important;
                color: white !important;
            }
        </style>
    </head>
    <body>
        <div class="container py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h3><i class="fas fa-folder-open"></i> Materials & Resources</h3>
                <div>
                    <a href="/director/upload" class="btn btn-primary btn-sm">
                        <i class="fas fa-upload"></i> Upload New
                    </a>
                    <a href="/director/director_dashboard" class="btn btn-secondary btn-sm">
                        <i class="fas fa-arrow-left"></i> Back
                    </a>
                </div>
            </div>
            
            <!-- Filter Bar -->
            <div class="row mb-3">
                <div class="col-md-4">
                    <form method="GET" class="d-flex">
                        <input type="text" name="search" class="form-control" placeholder="Search files..." value="{{ search }}">
                        <input type="hidden" name="page" value="1">
                        <input type="hidden" name="per_page" value="{{ per_page }}">
                        <button type="submit" class="btn btn-primary ms-2">
                            <i class="fas fa-search"></i>
                        </button>
                        {% if search %}
                            <a href="?per_page={{ per_page }}" class="btn btn-secondary ms-2">Clear</a>
                        {% endif %}
                    </form>
                </div>
                <div class="col-md-6">
                    <div class="btn-group">
                        <a href="?per_page={{ per_page }}" class="btn btn-outline-secondary btn-sm {% if not file_type %}active filter-active{% endif %}">
                            All
                        </a>
                        <a href="?type=pdf&per_page={{ per_page }}" class="btn btn-outline-secondary btn-sm {% if file_type == 'pdf' %}active filter-active{% endif %}">
                            PDF
                        </a>
                        <a href="?type=doc&per_page={{ per_page }}" class="btn btn-outline-secondary btn-sm {% if file_type == 'doc' %}active filter-active{% endif %}">
                            DOC
                        </a>
                        <a href="?type=xls&per_page={{ per_page }}" class="btn btn-outline-secondary btn-sm {% if file_type == 'xls' %}active filter-active{% endif %}">
                            XLS
                        </a>
                        <a href="?type=image&per_page={{ per_page }}" class="btn btn-outline-secondary btn-sm {% if file_type == 'image' %}active filter-active{% endif %}">
                            Image
                        </a>
                    </div>
                </div>
                <div class="col-md-2 text-end">
                    <select class="form-select form-select-sm d-inline-block w-auto" onchange="window.location.href='?per_page='+this.value">
                        <option value="10" {% if per_page == 10 %}selected{% endif %}>10 per page</option>
                        <option value="25" {% if per_page == 25 %}selected{% endif %}>25 per page</option>
                        <option value="50" {% if per_page == 50 %}selected{% endif %}>50 per page</option>
                        <option value="100" {% if per_page == 100 %}selected{% endif %}>100 per page</option>
                    </select>
                </div>
            </div>
            
            <div class="table-container">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>File Name</th>
                                <th>Type</th>
                                <th>Source</th>
                                <th>Size</th>
                                <th>Modified</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for material in paginated_materials %}
                            <tr>
                                <td>{{ start_show + loop.index0 }}</td>
                                <td>
                                    {% set ext = material.extension.lower() %}
                                    {% if ext == 'pdf' %}
                                        <i class="fas fa-file-pdf file-icon file-pdf"></i>
                                    {% elif ext in ['doc', 'docx'] %}
                                        <i class="fas fa-file-word file-icon file-doc"></i>
                                    {% elif ext in ['xls', 'xlsx'] %}
                                        <i class="fas fa-file-excel file-icon file-xls"></i>
                                    {% elif ext in ['ppt', 'pptx'] %}
                                        <i class="fas fa-file-powerpoint file-icon file-ppt"></i>
                                    {% elif ext in ['jpg', 'jpeg', 'png', 'gif'] %}
                                        <i class="fas fa-file-image file-icon file-img"></i>
                                    {% elif ext == 'txt' %}
                                        <i class="fas fa-file-alt file-icon file-txt"></i>
                                    {% else %}
                                        <i class="fas fa-file file-icon file-default"></i>
                                    {% endif %}
                                    {{ material.name }}
                                </td>
                                <td><span class="badge bg-secondary">{{ material.extension }}</span></td>
                                <td>
                                    {% if material.source == 'database' %}
                                        <span class="badge bg-info">Database</span>
                                    {% else %}
                                        <span class="badge bg-success">Uploaded</span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if material.size and material.size > 0 %}
                                        {{ "%.2f"|format(material.size / 1048576) }} MB
                                    {% else %}
                                        N/A
                                    {% endif %}
                                </td>
                                <td>{{ material.modified }}</td>
                                <td>
                                    <div class="d-flex gap-1 flex-wrap">
                                        {% if material.source == 'folder' %}
                                            <a href="/static/uploads/{{ material.path }}" class="btn btn-primary btn-sm btn-download" download>
                                                <i class="fas fa-download"></i> Download
                                            </a>
                                            <button class="btn btn-danger btn-sm btn-delete"
                                                data-id="{{ material.path }}"
                                                data-name="{{ material.name | e }}"
                                                data-type="file">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        {% else %}
                                            <a href="/director/download/{{ material.sanitized_name }}" class="btn btn-primary btn-sm btn-download">
                                                <i class="fas fa-download"></i> Download
                                            </a>
                                            {% if material.id is not none %}
                                            <button class="btn btn-danger btn-sm btn-delete"
                                                data-id="{{ material.id }}"
                                                data-name="{{ material.name | e }}"
                                                data-type="db">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                            {% endif %}
                                        {% endif %}
                                    </div>
                                </td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="7" class="text-center">
                                    <i class="fas fa-folder-open fa-2x text-muted mb-2 d-block"></i>
                                    No files found. <a href="/director/upload">Upload your first file</a>
                                </td>
                            </td>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                
                <!-- Pagination & File Info Footer -->
                <div class="d-flex justify-content-between align-items-center mt-3 flex-wrap gap-2">
                    <!-- Left: file name + size info for current page -->
                    <div class="text-muted small">
                        {% if total_count > 0 %}
                            Showing <strong>{{ start_show }}</strong>–<strong>{{ end_show }}</strong> of <strong>{{ total_count }}</strong> file{{ 's' if total_count != 1 else '' }}
                            &nbsp;&bull;&nbsp;
                            {% set ns = namespace(total_bytes=0) %}
                            {% for material in paginated_materials %}
                                {% if material.size and material.size != 'N/A' %}
                                    {% set ns.total_bytes = ns.total_bytes + material.size %}
                                {% endif %}
                            {% endfor %}
                            Page size: {{ "%.2f"|format(ns.total_bytes / 1048576) }} MB
                            &nbsp;&bull;&nbsp; Page <strong>{{ page }}</strong> of <strong>{{ total_pages }}</strong>
                        {% else %}
                            No files found
                        {% endif %}
                    </div>

                    <!-- Right: pagination controls (always visible) -->
                    <nav>
                        <ul class="pagination pagination-sm mb-0">
                            {% if page > 1 %}
                            <li class="page-item">
                                <a class="page-link" href="?page=1&per_page={{ per_page }}{% if search %}&search={{ search }}{% endif %}{% if file_type %}&type={{ file_type }}{% endif %}" title="First page">
                                    <i class="fas fa-angle-double-left"></i>
                                </a>
                            </li>
                            <li class="page-item">
                                <a class="page-link" href="?page={{ page-1 }}&per_page={{ per_page }}{% if search %}&search={{ search }}{% endif %}{% if file_type %}&type={{ file_type }}{% endif %}" title="Previous page">
                                    <i class="fas fa-angle-left"></i>
                                </a>
                            </li>
                            {% else %}
                            <li class="page-item disabled"><span class="page-link"><i class="fas fa-angle-double-left"></i></span></li>
                            <li class="page-item disabled"><span class="page-link"><i class="fas fa-angle-left"></i></span></li>
                            {% endif %}

                            {% for p in page_range %}
                                {% if p == page %}
                                <li class="page-item active"><span class="page-link">{{ p }}</span></li>
                                {% else %}
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ p }}&per_page={{ per_page }}{% if search %}&search={{ search }}{% endif %}{% if file_type %}&type={{ file_type }}{% endif %}">{{ p }}</a>
                                </li>
                                {% endif %}
                            {% endfor %}

                            {% if page < total_pages %}
                            <li class="page-item">
                                <a class="page-link" href="?page={{ page+1 }}&per_page={{ per_page }}{% if search %}&search={{ search }}{% endif %}{% if file_type %}&type={{ file_type }}{% endif %}" title="Next page">
                                    <i class="fas fa-angle-right"></i>
                                </a>
                            </li>
                            <li class="page-item">
                                <a class="page-link" href="?page={{ total_pages }}&per_page={{ per_page }}{% if search %}&search={{ search }}{% endif %}{% if file_type %}&type={{ file_type }}{% endif %}" title="Last page">
                                    <i class="fas fa-angle-double-right"></i>
                                </a>
                            </li>
                            {% else %}
                            <li class="page-item disabled"><span class="page-link"><i class="fas fa-angle-right"></i></span></li>
                            <li class="page-item disabled"><span class="page-link"><i class="fas fa-angle-double-right"></i></span></li>
                            {% endif %}
                        </ul>
                    </nav>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>

        <div class="modal fade" id="deleteModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title text-danger"><i class="fas fa-trash"></i> Delete File</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        Are you sure you want to delete <strong id="deleteFileName"></strong>?
                        <br><small class="text-muted">This will permanently remove the file from disk and database.</small>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <a id="deleteConfirmBtn" href="#" class="btn btn-danger"><i class="fas fa-trash"></i> Delete</a>
                    </div>
                </div>
            </div>
        </div>
        <script>
            document.querySelectorAll('.btn-delete').forEach(function(btn) {
                btn.addEventListener('click', function() {
                    var id   = this.getAttribute('data-id');
                    var name = this.getAttribute('data-name');
                    var type = this.getAttribute('data-type');
                    document.getElementById('deleteFileName').textContent = name;
                    var url = type === 'db'
                        ? '/director/materials/delete/' + id
                        : '/director/materials/delete-file/' + encodeURIComponent(id);
                    document.getElementById('deleteConfirmBtn').href = url;
                    new bootstrap.Modal(document.getElementById('deleteModal')).show();
                });
            });
        </script>
    </body>
    </html>
    ''',
    paginated_materials=paginated_materials,
    total_count=total_count,
    total_pages=total_pages,
    page=page,
    per_page=per_page,
    start_show=start_show,
    end_show=end_show,
    page_range=page_range,
    search=search,
    file_type=file_type
    )


@director_materials.route('/materials/debug')
@login_required
def materials_debug():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SHOW COLUMNS FROM materials")
    columns = [row['Field'] for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM materials ORDER BY id DESC LIMIT 3")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    output = "<h2>Columns in <code>materials</code> table:</h2>"
    output += "<pre>" + "\n".join(columns) + "</pre>"
    output += "<h2>First 3 rows:</h2>"
    for row in rows:
        output += "<pre>"
        for col, val in row.items():
            output += f"{col}: {repr(val)}\n"
        output += "</pre><hr>"

    # Also check what files exist on disk
    output += "<h2>Files in upload folder:</h2><pre>"
    if os.path.exists(UPLOAD_FOLDER):
        for f in os.listdir(UPLOAD_FOLDER)[:10]:
            fp = os.path.join(UPLOAD_FOLDER, f)
            if os.path.isfile(fp):
                output += f"{f} ({os.stat(fp).st_size} bytes)\n"
    output += "</pre>"
    return output

@director_materials.route('/download/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@director_materials.route('/materials/delete/<material_id>')
@login_required
def delete_material(material_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT file_path FROM materials WHERE ID = %s", (material_id,))
        row = cursor.fetchone()
        if row and row.get('file_path'):
            file_on_disk = os.path.join(UPLOAD_FOLDER, os.path.basename(row['file_path']))
            if os.path.isfile(file_on_disk):
                os.remove(file_on_disk)
        cursor.execute("DELETE FROM materials WHERE ID = %s", (material_id,))
        conn.commit()
    except Exception as e:
        print(f"Delete error: {e}")
    finally:
        cursor.close()
        conn.close()
    return redirect('/director/materials')


@director_materials.route('/materials/delete-file/<path:filename>')
@login_required
def delete_folder_file(filename):
    try:
        file_on_disk = os.path.join(UPLOAD_FOLDER, os.path.basename(filename))
        if os.path.isfile(file_on_disk):
            os.remove(file_on_disk)
    except Exception as e:
        print(f"Delete file error: {e}")
    return redirect('/director/materials')