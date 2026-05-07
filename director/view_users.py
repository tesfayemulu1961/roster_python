from flask import Blueprint, request, session, redirect, url_for, render_template_string
import mysql.connector
from datetime import datetime

# Create blueprint
view_users_bp = Blueprint('view_users', __name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Accounts Management</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background-color: #f5f7fa;
            color: #333;
            padding: 20px;
        }
        
        .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .page-header h1 {
            color: #2c3e50;
            font-size: 28px;
        }
        
        .page-header h1 i {
            margin-right: 10px;
            color: #4a6fa5;
        }
        
        .user-controls {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .user-search-form {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .form-group {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .form-control {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            min-width: 200px;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            text-decoration: none;
            transition: all 0.3s;
        }
        
        .btn-search {
            background-color: #4a6fa5;
            color: white;
        }
        
        .btn-filter {
            background-color: #6f4a8c;
            color: white;
        }
        
        .btn-add-user {
            background-color: #28a745;
            color: white;
        }
        
        .btn-back {
            background-color: #6c757d;
            color: white;
        }
        
        .btn:hover {
            opacity: 0.9;
            transform: translateY(-2px);
        }
        
        .user-table-container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            padding: 20px;
            overflow-x: auto;
        }
        
        .user-table {
            width: 100%;
            min-width: 1000px;
            border-collapse: collapse;
        }
        
        .user-table th {
            background-color: #f8f9fa;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            position: sticky;
            top: 0;
        }
        
        .user-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            vertical-align: middle;
        }
        
        .user-table tr:hover {
            background-color: #f8f9fa;
        }
        
        .user-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            text-transform: capitalize;
        }
        
        .user-type-director, .user-type-admin {
            background-color: #dc3545;
            color: white;
        }
        
        .user-type-vice_director {
            background-color: #d35400;
            color: white;
        }
        
        .user-type-supervisor {
            background-color: #e67e22;
            color: white;
        }
        
        .user-type-room_teacher, .user-type-subject_teacher {
            background-color: #007bff;
            color: white;
        }
        
        .user-type-student {
            background-color: #28a745;
            color: white;
        }
        
        .user-type-parent {
            background-color: #6f42c1;
            color: white;
        }
        
        .account-status-active {
            background-color: #28a745;
            color: white;
        }
        
        .account-status-inactive {
            background-color: #6c757d;
            color: white;
        }
        
        .account-status-suspended {
            background-color: #ffc107;
            color: #212529;
        }
        
        .actions {
            display: flex;
            gap: 8px;
        }
        
        .btn-action {
            padding: 6px;
            border-radius: 4px;
            color: white;
            width: 30px;
            height: 30px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        
        .btn-edit {
            background-color: #ffc107;
        }
        
        .btn-delete {
            background-color: #dc3545;
        }
        
        .btn-action:hover {
            transform: scale(1.1);
        }
        
        .alert {
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        
        .alert-danger {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            margin-top: 20px;
            gap: 5px;
        }
        
        .pagination a, .pagination span {
            padding: 8px 12px;
            border: 1px solid #ddd;
            text-decoration: none;
            color: #4a6fa5;
            border-radius: 4px;
        }
        
        .pagination a:hover {
            background-color: #f5f7fa;
        }
        
        .pagination .current {
            background-color: #4a6fa5;
            color: white;
            border-color: #4a6fa5;
        }
        
        .pagination .disabled {
            color: #ccc;
            pointer-events: none;
        }
        
        @media (max-width: 768px) {
            .user-controls {
                flex-direction: column;
            }
            
            .user-search-form {
                width: 100%;
            }
            
            .form-group {
                width: 100%;
            }
            
            .form-control {
                flex: 1;
            }
            
            .btn-add-user {
                width: 100%;
                text-align: center;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="page-header">
        <h1><i class="fas fa-users"></i> User Accounts</h1>
        <a href="/director/director_dashboard" class="btn btn-back"><i class="fas fa-arrow-left"></i> Back to Dashboard</a>
    </div>
    
    <div class="user-controls">
        <form method="get" class="user-search-form">
            <div class="form-group">
                <input type="text" name="search" placeholder="Search by username" 
                       value="{{ search_term }}" class="form-control">
                <button type="submit" class="btn btn-search"><i class="fas fa-search"></i> Search</button>
            </div>
            
            <div class="form-group">
                <select name="user_type" class="form-control">
                    <option value="">All User Types</option>
                    <option value="admin" {{ 'selected' if user_type_filter == 'admin' else '' }}>Administrators</option>
                    <option value="director" {{ 'selected' if user_type_filter == 'director' else '' }}>Directors</option>
                    <option value="room_teacher" {{ 'selected' if user_type_filter == 'room_teacher' else '' }}>Room Teachers</option>
                    <option value="subject_teacher" {{ 'selected' if user_type_filter == 'subject_teacher' else '' }}>Subject Teachers</option>
                    <option value="vice_director" {{ 'selected' if user_type_filter == 'vice_director' else '' }}>Vice Directors</option>
                    <option value="supervisor" {{ 'selected' if user_type_filter == 'supervisor' else '' }}>Supervisors</option>
                    <option value="student" {{ 'selected' if user_type_filter == 'student' else '' }}>Students</option>
                    <option value="parent" {{ 'selected' if user_type_filter == 'parent' else '' }}>Parents</option>
                </select>
                <button type="submit" class="btn btn-filter"><i class="fas fa-filter"></i> Filter</button>
            </div>
            <input type="hidden" name="page" value="1">
        </form>
        
        <a href="/director/insert_users" class="btn btn-add-user"><i class="fas fa-user-plus"></i> Add New User</a>
    </div>
    
    <div class="user-table-container">
    {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
    {% elif not users %}
        <div class="alert alert-info">No users found matching your criteria</div>
    {% else %}
        <table class="user-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>User Type</th>
                    <th>Last Login</th>
                    <th>Account Status</th>
                    <th>Created</th>
                    <th>Updated</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for user in users %}
                <tr>
                    <td>{{ user.user_id }}</td>
                    <td>{{ user.username }}</td>
                    <td>
                            {% set display_type = user.user_type %}
                            {% if 'room_teacher' in display_type %}
                                {% set display_type = 'Room Teacher' %}
                            {% elif 'subject_teacher' in display_type %}
                                {% set display_type = 'Subject Teacher' %}
                            {% elif display_type == 'vice_director' %}
                                {% set display_type = 'Vice Director' %}
                            {% else %}
                                {% set display_type = display_type|capitalize %}
                            {% endif %}
                            <span class="user-badge user-type-{{ user.user_type }}">
                                {{ display_type }}
                            </span>
                        </td>
                        <td>{{ user.last_login_formatted if user.last_login else 'Never' }}</td>
                        <td>
                            <span class="user-badge account-status-{{ user.account_status }}">
                                {{ user.account_status|capitalize }}
                            </span>
                        </td>
                        <td>{{ user.created_at_formatted }}</td>
                        <td>{{ user.updated_at_formatted }}</td>
                        <td class="actions">
                            <a href="/director/edit_user?id={{ user.user_id }}" class="btn-action btn-edit" title="Edit">
                                <i class="fas fa-edit"></i>
                            </a>
                            <a href="/director/view_users?delete={{ user.user_id }}" class="btn-action btn-delete" title="Delete" 
                               onclick="return confirm('Are you sure you want to delete this user?');">
                                <i class="fas fa-trash-alt"></i>
                            </a>
                        </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <div class="pagination">
            {% if current_page > 1 %}
                <a href="?page=1&search={{ search_term }}&user_type={{ user_type_filter }}">
                    <i class="fas fa-angle-double-left"></i>
                </a>
                <a href="?page={{ current_page - 1 }}&search={{ search_term }}&user_type={{ user_type_filter }}">
                    <i class="fas fa-angle-left"></i>
                </a>
            {% else %}
                <span class="disabled"><i class="fas fa-angle-double-left"></i></span>
                <span class="disabled"><i class="fas fa-angle-left"></i></span>
            {% endif %}
            
            {% for page_num in page_range %}
                {% if page_num == current_page %}
                    <span class="current">{{ page_num }}</span>
                {% else %}
                    <a href="?page={{ page_num }}&search={{ search_term }}&user_type={{ user_type_filter }}">{{ page_num }}</a>
                {% endif %}
            {% endfor %}
            
            {% if current_page < total_pages %}
                <a href="?page={{ current_page + 1 }}&search={{ search_term }}&user_type={{ user_type_filter }}">
                    <i class="fas fa-angle-right"></i>
                </a>
                <a href="?page={{ total_pages }}&search={{ search_term }}&user_type={{ user_type_filter }}">
                    <i class="fas fa-angle-double-right"></i>
                </a>
            {% else %}
                <span class="disabled"><i class="fas fa-angle-right"></i></span>
                <span class="disabled"><i class="fas fa-angle-double-right"></i></span>
            {% endif %}
        </div>
        
        <div style="text-align: center; margin-top: 10px; color: #666;">
            Showing {{ offset + 1 }} to {{ offset + per_page if offset + per_page <= total_users else total_users }} of {{ total_users }} users
        </div>
    {% endif %}
    </div>
</body>
</html>
"""

@view_users_bp.route('/director/view_users', methods=['GET'])
def view_users():
    """View user accounts with pagination, search, and filters"""
    
    # Check if user is logged in as director
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return redirect(url_for('unauthorized'))
    
    # Handle delete action
    delete_id = request.args.get('delete')
    if delete_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE user_id = %s", (delete_id,))
            conn.commit()
        except Exception as e:
            print(f"Error deleting user: {e}")
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('view_users.view_users'))
    
    # Get filter parameters
    search_term = request.args.get('search', '').strip()
    user_type_filter = request.args.get('user_type', '')
    current_page = request.args.get('page', 1, type=int)
    if current_page < 1:
        current_page = 1
    
    per_page = 10
    offset = (current_page - 1) * per_page
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Build count query for pagination
        count_sql = "SELECT COUNT(*) as total FROM users WHERE 1=1"
        count_params = []
        
        if search_term:
            count_sql += " AND username LIKE %s"
            count_params.append(f"%{search_term}%")
        
        if user_type_filter:
            if user_type_filter == 'admin':
                count_sql += " AND (user_type LIKE 'admin' OR user_type LIKE 'director')"
            elif user_type_filter == 'teacher':
                count_sql += " AND (user_type LIKE 'room_teacher' OR user_type LIKE 'subject_teacher')"
            elif user_type_filter == 'room_teacher':
                count_sql += " AND user_type LIKE %s"
                count_params.append("%room_teacher%")
            elif user_type_filter == 'subject_teacher':
                count_sql += " AND user_type LIKE %s"
                count_params.append("%subject_teacher%")
            else:
                count_sql += " AND user_type LIKE %s"
                count_params.append(f"%{user_type_filter}%")
        
        cursor.execute(count_sql, count_params)
        total_users = cursor.fetchone()['total']
        
        # Build main query
        sql = "SELECT user_id, username, user_type, created_at, last_login, account_status, updated_at FROM users WHERE 1=1"
        params = []
        
        if search_term:
            sql += " AND username LIKE %s"
            params.append(f"%{search_term}%")
        
        if user_type_filter:
            if user_type_filter == 'admin':
                sql += " AND (user_type LIKE 'admin' OR user_type LIKE 'director')"
            elif user_type_filter == 'teacher':
                sql += " AND (user_type LIKE 'room_teacher' OR user_type LIKE 'subject_teacher')"
            elif user_type_filter == 'room_teacher':
                sql += " AND user_type LIKE %s"
                params.append("%room_teacher%")
            elif user_type_filter == 'subject_teacher':
                sql += " AND user_type LIKE %s"
                params.append("%subject_teacher%")
            else:
                sql += " AND user_type LIKE %s"
                params.append(f"%{user_type_filter}%")
        
        sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cursor.execute(sql, params)
        users = cursor.fetchall()
        
        # Format dates for display
        for user in users:
            if user.get('last_login'):
                if isinstance(user['last_login'], datetime):
                    user['last_login_formatted'] = user['last_login'].strftime('%b %j, %Y %I:%M %p')
                else:
                    user['last_login_formatted'] = str(user['last_login'])
            else:
                user['last_login_formatted'] = None
            
            for date_field in ['created_at', 'updated_at']:
                if user.get(date_field):
                    if isinstance(user[date_field], datetime):
                        user[f'{date_field}_formatted'] = user[date_field].strftime('%b %j, %Y')
                    else:
                        user[f'{date_field}_formatted'] = str(user[date_field])[:10]
                else:
                    user[f'{date_field}_formatted'] = 'N/A'
        
    except Exception as e:
        print(f"Database error: {e}")
        error = "Error loading user data. Please try again."
        users = []
        total_users = 0
    finally:
        cursor.close()
        conn.close()
    
    # Calculate pagination
    total_pages = (total_users + per_page - 1) // per_page if total_users > 0 else 1
    
    # Generate page range for pagination
    max_links = 5
    start_page = max(1, current_page - max_links // 2)
    end_page = min(total_pages, start_page + max_links - 1)
    
    if end_page - start_page + 1 < max_links:
        start_page = max(1, end_page - max_links + 1)
    
    page_range = list(range(start_page, end_page + 1))
    
    error = locals().get('error', '')
    
    return render_template_string(
        HTML_TEMPLATE,
        users=users,
        total_users=total_users,
        current_page=current_page,
        total_pages=total_pages,
        per_page=per_page,
        offset=offset,
        search_term=search_term,
        user_type_filter=user_type_filter,
        page_range=page_range,
        error=error
    )


print("✅ view_users.py blueprint loaded")
print("   📌 Route: /director/view_users")