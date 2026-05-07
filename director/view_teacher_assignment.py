# ==============================================
# View Teacher Assignments - Professional Clean Display
# ==============================================

from flask import Blueprint, render_template_string, session, redirect, request
from functools import wraps
import mysql.connector
import math

director_view_teacher_assignment = Blueprint('director_view_teacher_assignment', __name__, url_prefix='/director')

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

@director_view_teacher_assignment.route('/view_teacher_assignment')
@login_required
def view_teacher_assignment_page():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    search = request.args.get('search', '', type=str)
    assignment_type = request.args.get('assignment_type', '')
    offset = (page - 1) * per_page
    
    where_clause = "1=1"
    params = []
    
    if search:
        where_clause += " AND (t.name LIKE %s OR t.t_id LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param])
    
    if assignment_type:
        if assignment_type == 'room':
            where_clause += " AND ta.is_room_teacher = 1"
        elif assignment_type == 'subject':
            where_clause += " AND ta.is_subject_teacher = 1"
    
    count_query = f"""
        SELECT COUNT(*) as total FROM teacher_assignment ta
        JOIN teacher t ON ta.teacher_id = t.ID
        WHERE {where_clause}
    """
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()['total']
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    
    query = f"""
        SELECT 
            ta.ID, ta.teacher_id, ta.grade_id, ta.section_id, ta.subject_id,
            ta.academic_year_id, ta.is_room_teacher, ta.is_subject_teacher,
            t.name as teacher_name, t.t_id as teacher_code,
            g.level as grade_name,
            s.sec_name as section_name,
            sub.sub_name as subject_name,
            ay.year as academic_year
        FROM teacher_assignment ta
        JOIN teacher t ON ta.teacher_id = t.ID
        LEFT JOIN grade g ON ta.grade_id = g.ID
        LEFT JOIN section s ON ta.section_id = s.ID
        LEFT JOIN subject sub ON ta.subject_id = sub.id
        LEFT JOIN academic_year ay ON ta.academic_year_id = ay.ID
        WHERE {where_clause}
        ORDER BY ta.ID DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, params + [per_page, offset])
    assignments = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Teacher Assignments</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="/static/css/core.css">
        <style>
            * {
                font-family: 'Inter', sans-serif;
            }
            
            body {
                background: #f5f7fa;
                padding: 30px 0;
            }
            
            .container-narrow {
                max-width: 1000px;
                margin: 0 auto;
            }
            
            .header-section {
                background: white;
                border-radius: 8px;
                padding: 20px 25px;
                margin-bottom: 20px;
                border: 1px solid #e4e7ed;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }
            
            .page-title {
                font-size: 1.25rem;
                font-weight: 600;
                color: #2c3e50;
                margin: 0;
            }
            
            .btn-primary-clean {
                background: #fff;
                border: 1px solid #dcdfe6;
                color: #606266;
                padding: 6px 14px;
                font-size: 0.85rem;
                border-radius: 6px;
                transition: all 0.2s;
            }
            
            .btn-primary-clean:hover {
                background: #f5f7fa;
                border-color: #c0c4cc;
                color: #2c3e50;
            }
            
            .filter-card {
                background: white;
                border-radius: 8px;
                padding: 20px 25px;
                margin-bottom: 20px;
                border: 1px solid #e4e7ed;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }
            
            .form-control, .form-select {
                border-radius: 6px;
                border: 1px solid #dcdfe6;
                font-size: 0.85rem;
                padding: 8px 12px;
            }
            
            .form-control:focus, .form-select:focus {
                border-color: #409eff;
                box-shadow: 0 0 0 2px rgba(64,158,255,0.1);
            }
            
            .btn-apply {
                background: #409eff;
                border: none;
                color: white;
                padding: 8px 20px;
                font-size: 0.85rem;
                border-radius: 6px;
                font-weight: 500;
            }
            
            .btn-apply:hover {
                background: #66b1ff;
            }
            
            .assignment-item {
                background: white;
                border-radius: 8px;
                margin-bottom: 10px;
                border: 1px solid #e4e7ed;
                transition: all 0.2s;
                box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            }
            
            .assignment-item:hover {
                background: #fafbfc;
                border-color: #dcdfe6;
            }
            
            .assignment-row {
                padding: 14px 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 10px;
            }
            
            .teacher-info {
                flex: 2;
                min-width: 200px;
            }
            
            .teacher-name {
                font-weight: 600;
                color: #2c3e50;
                font-size: 0.95rem;
                margin-bottom: 4px;
            }
            
            .teacher-code {
                font-size: 0.75rem;
                color: #909399;
            }
            
            .assignment-details {
                flex: 3;
                display: flex;
                gap: 20px;
                flex-wrap: wrap;
                align-items: center;
            }
            
            .detail-item {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 0.8rem;
                color: #606266;
            }
            
            .detail-item i {
                color: #909399;
                width: 14px;
                font-size: 0.75rem;
            }
            
            .badge-type {
                padding: 3px 10px;
                border-radius: 4px;
                font-size: 0.7rem;
                font-weight: 500;
            }
            
            .badge-room {
                background: #ecf5ff;
                color: #409eff;
            }
            
            .badge-subject {
                background: #f0f9ff;
                color: #67c23a;
            }
            
            .stats-bar {
                display: flex;
                gap: 30px;
                align-items: center;
                flex-wrap: wrap;
            }
            
            .stat-badge {
                font-size: 0.8rem;
                color: #606266;
            }
            
            .stat-badge strong {
                color: #2c3e50;
                font-weight: 600;
                margin-right: 4px;
            }
            
            .pagination-wrapper {
                display: flex;
                justify-content: center;
                gap: 6px;
                margin-top: 25px;
            }
            
            .page-btn {
                padding: 6px 12px;
                background: white;
                border: 1px solid #dcdfe6;
                color: #606266;
                text-decoration: none;
                font-size: 0.8rem;
                border-radius: 4px;
                transition: all 0.2s;
            }
            
            .page-btn:hover {
                background: #f5f7fa;
                border-color: #c0c4cc;
                color: #409eff;
            }
            
            .page-btn.active {
                background: #409eff;
                border-color: #409eff;
                color: white;
            }
            
            .empty-state {
                background: white;
                border-radius: 8px;
                padding: 50px 20px;
                text-align: center;
                border: 1px solid #e4e7ed;
                color: #909399;
            }
            
            .separator {
                color: #dcdfe6;
                padding: 0 5px;
            }
            
            @media (max-width: 768px) {
                .assignment-row {
                    flex-direction: column;
                    align-items: stretch;
                }
                
                .assignment-details {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 8px;
                }
                
                .stats-bar {
                    gap: 15px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container-narrow">
            <!-- Header -->
            <div class="header-section">
                <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                    <div>
                        <h1 class="page-title">
                            <i class="fas fa-tasks" style="color: #909399; margin-right: 8px;"></i>
                            Teacher Assignments
                        </h1>
                    </div>
                    <div class="d-flex gap-2">
                        <a href="/director/insert_teacher_assignment" class="btn-primary-clean text-decoration-none">
                            <i class="fas fa-plus"></i> New Assignment
                        </a>
                        <a href="/director/director_dashboard" class="btn-primary-clean text-decoration-none">
                            <i class="fas fa-arrow-left"></i> Back
                        </a>
                    </div>
                </div>
                
                <!-- Mini Stats -->
                <div class="stats-bar mt-3 pt-2">
                    <div class="stat-badge">
                        <strong>{{ assignments|length }}</strong> on this page
                    </div>
                    <span class="separator">|</span>
                    <div class="stat-badge">
                        <strong>{{ total_count }}</strong> total assignments
                    </div>
                    <span class="separator">|</span>
                    <div class="stat-badge">
                        <strong>{{ total_pages }}</strong> pages
                    </div>
                </div>
            </div>
            
            <!-- Filters -->
            <div class="filter-card">
                <form method="GET" class="row g-2">
                    <div class="col-md-5">
                        <div class="input-group">
                            <span class="input-group-text bg-white" style="border-radius: 6px 0 0 6px; border-right: none;">
                                <i class="fas fa-search" style="color: #909399;"></i>
                            </span>
                            <input type="text" name="search" class="form-control" 
                                   placeholder="Teacher name or code..." value="{{ search }}"
                                   style="border-left: none;">
                        </div>
                    </div>
                    <div class="col-md-3">
                        <select name="assignment_type" class="form-select">
                            <option value="">All types</option>
                            <option value="room" {% if assignment_type == 'room' %}selected{% endif %}>Room teachers</option>
                            <option value="subject" {% if assignment_type == 'subject' %}selected{% endif %}>Subject teachers</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <select name="per_page" class="form-select">
                            <option value="15" {% if per_page == 15 %}selected{% endif %}>15 per page</option>
                            <option value="25" {% if per_page == 25 %}selected{% endif %}>25 per page</option>
                            <option value="50" {% if per_page == 50 %}selected{% endif %}>50 per page</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn-apply w-100">
                            <i class="fas fa-filter"></i> Apply
                        </button>
                    </div>
                </form>
            </div>
            
            <!-- Assignments List -->
            {% for assign in assignments %}
            <div class="assignment-item">
                <div class="assignment-row">
                    <div class="teacher-info">
                        <div class="teacher-name">
                            {{ assign.teacher_name }}
                        </div>
                        <div class="teacher-code">
                            ID: {{ assign.teacher_code }}
                        </div>
                    </div>
                    
                    <div class="assignment-details">
                        <div class="detail-item">
                            <i class="fas fa-graduation-cap"></i>
                            <span>{{ assign.grade_name or '—' }}</span>
                        </div>
                        <div class="detail-item">
                            <i class="fas fa-door-open"></i>
                            <span>{{ assign.section_name or '—' }}</span>
                        </div>
                        <div class="detail-item">
                            <i class="fas fa-book"></i>
                            <span>{{ assign.subject_name or '—' }}</span>
                        </div>
                        <div class="detail-item">
                            <i class="fas fa-calendar"></i>
                            <span>{{ assign.academic_year or '—' }}</span>
                        </div>
                        <div>
                            {% if assign.is_room_teacher %}
                            <span class="badge-type badge-room">Room Teacher</span>
                            {% else %}
                            <span class="badge-type badge-subject">Subject Teacher</span>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            {% else %}
            <div class="empty-state">
                <i class="fas fa-inbox" style="font-size: 2rem; margin-bottom: 12px; opacity: 0.5;"></i>
                <p style="margin: 0;">No assignments found</p>
                <small class="text-muted">Try adjusting your search or filter criteria</small>
            </div>
            {% endfor %}
            
            <!-- Pagination -->
            {% if total_pages > 1 %}
            <div class="pagination-wrapper">
                {% if page > 1 %}
                <a href="?page={{ page-1 }}&per_page={{ per_page }}&search={{ search }}&assignment_type={{ assignment_type }}" 
                   class="page-btn">
                    <i class="fas fa-chevron-left"></i>
                </a>
                {% endif %}
                
                {% set start_page = [page-2, 1]|max %}
                {% set end_page = [page+2, total_pages]|min %}
                
                {% for p in range(start_page, end_page + 1) %}
                    {% if p == page %}
                    <span class="page-btn active">{{ p }}</span>
                    {% else %}
                    <a href="?page={{ p }}&per_page={{ per_page }}&search={{ search }}&assignment_type={{ assignment_type }}" 
                       class="page-btn">{{ p }}</a>
                    {% endif %}
                {% endfor %}
                
                {% if page < total_pages %}
                <a href="?page={{ page+1 }}&per_page={{ per_page }}&search={{ search }}&assignment_type={{ assignment_type }}" 
                   class="page-btn">
                    <i class="fas fa-chevron-right"></i>
                </a>
                {% endif %}
            </div>
            {% endif %}
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="/static/js/core.js"></script>
    </body>
    </html>
    ''',
    assignments=assignments, page=page, total_pages=total_pages, per_page=per_page,
    total_count=total_count, search=search, assignment_type=assignment_type
    )