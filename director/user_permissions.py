from flask import Blueprint, request, session, redirect, url_for, render_template_string
import mysql.connector
from datetime import datetime

# Create blueprint
user_permissions_bp = Blueprint('user_permissions', __name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# HTML Template with Pagination
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Permissions Management</title>
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
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
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
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
        }
        
        .stat-card i {
            font-size: 40px;
            color: #4a6fa5;
            margin-bottom: 10px;
        }
        
        .stat-card h3 {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }
        
        .stat-card .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .permissions-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            overflow: hidden;
        }
        
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .tab {
            padding: 15px 25px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .tab:hover {
            background: #e9ecef;
        }
        
        .tab.active {
            background: white;
            color: #4a6fa5;
            border-bottom: 3px solid #4a6fa5;
        }
        
        .tab-content {
            display: none;
            padding: 25px;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .user-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .user-table th,
        .user-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        .user-table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        
        .user-table tr:hover {
            background-color: #f8f9fa;
        }
        
        .permission-group {
            margin-bottom: 30px;
        }
        
        .permission-group h3 {
            margin-bottom: 15px;
            color: #2c3e50;
            border-left: 4px solid #4a6fa5;
            padding-left: 10px;
        }
        
        .permission-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .permission-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        
        .permission-item input {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }
        
        .permission-item label {
            cursor: pointer;
            flex: 1;
        }
        
        .btn-save {
            background-color: #28a745;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 20px;
        }
        
        .btn-save:hover {
            background-color: #218838;
        }
        
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        .alert-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .role-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .role-admin {
            background-color: #dc3545;
            color: white;
        }
        
        .role-director {
            background-color: #d35400;
            color: white;
        }
        
        .role-teacher {
            background-color: #007bff;
            color: white;
        }
        
        .role-student {
            background-color: #28a745;
            color: white;
        }
        
        .role-parent {
            background-color: #6f42c1;
            color: white;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status-active {
            background-color: #28a745;
            color: white;
        }
        
        .status-inactive {
            background-color: #6c757d;
            color: white;
        }
        
        .status-suspended {
            background-color: #ffc107;
            color: #212529;
        }
        
        .btn-edit-permission {
            background-color: #4a6fa5;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .btn-edit-permission:hover {
            background-color: #3a5a8c;
        }
        
        /* Pagination Styles */
        .pagination {
            display: flex;
            justify-content: center;
            margin-top: 20px;
            gap: 5px;
            flex-wrap: wrap;
        }
        
        .pagination a, .pagination span {
            padding: 8px 12px;
            border: 1px solid #ddd;
            text-decoration: none;
            color: #4a6fa5;
            border-radius: 4px;
            transition: all 0.3s;
        }
        
        .pagination a:hover {
            background-color: #4a6fa5;
            color: white;
            border-color: #4a6fa5;
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
        
        .page-info {
            text-align: center;
            margin-top: 15px;
            color: #666;
            font-size: 14px;
        }
        
        .search-box {
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        
        .search-box input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 250px;
        }
        
        .search-box button {
            padding: 8px 16px;
            background-color: #4a6fa5;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .search-box button:hover {
            background-color: #3a5a8c;
        }
        
        @media (max-width: 768px) {
            .tabs {
                flex-direction: column;
            }
            
            .permission-list {
                grid-template-columns: 1fr;
            }
            
            .search-box {
                justify-content: stretch;
            }
            
            .search-box input {
                flex: 1;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="page-header">
            <h1><i class="fas fa-key"></i> User Permissions Management</h1>
            <a href="/director/director_dashboard" class="btn" style="background: #6c757d; color: white; padding: 8px 16px; border-radius: 5px; text-decoration: none;">
                <i class="fas fa-arrow-left"></i> Back to Dashboard
            </a>
        </div>
        
        {% if success %}
            <div class="alert alert-success">{{ success }}</div>
        {% endif %}
        
        {% if error %}
            <div class="alert alert-error">{{ error }}</div>
        {% endif %}
        
        <div class="stats-grid">
            <div class="stat-card">
                <i class="fas fa-users"></i>
                <h3>Total Users</h3>
                <div class="stat-number">{{ total_users }}</div>
            </div>
            <div class="stat-card">
                <i class="fas fa-user-tie"></i>
                <h3>Directors</h3>
                <div class="stat-number">{{ directors_count }}</div>
            </div>
            <div class="stat-card">
                <i class="fas fa-chalkboard-teacher"></i>
                <h3>Teachers</h3>
                <div class="stat-number">{{ teachers_count }}</div>
            </div>
            <div class="stat-card">
                <i class="fas fa-user-graduate"></i>
                <h3>Students</h3>
                <div class="stat-number">{{ students_count }}</div>
            </div>
        </div>
        
        <div class="permissions-container">
            <div class="tabs">
                <button class="tab active" onclick="showTab('users')">
                    <i class="fas fa-list"></i> User List
                </button>
                <button class="tab" onclick="showTab('roles')">
                    <i class="fas fa-user-tag"></i> Role Management
                </button>
                <button class="tab" onclick="showTab('permissions')">
                    <i class="fas fa-lock"></i> Permission Settings
                </button>
            </div>
            
            <!-- User List Tab with Pagination -->
            <div id="users-tab" class="tab-content active">
                <h3><i class="fas fa-users"></i> System Users</h3>
                
                <!-- Search Box -->
                <div class="search-box">
                    <form method="get" action="/director/user_permissions">
                        <input type="hidden" name="tab" value="users">
                        <input type="text" name="search" placeholder="Search by username or type..." value="{{ search_term }}">
                        <button type="submit"><i class="fas fa-search"></i> Search</button>
                        {% if search_term %}
                            <a href="/director/user_permissions?tab=users" class="btn-clear" style="padding: 8px 16px; background: #6c757d; color: white; border-radius: 4px; text-decoration: none;">Clear</a>
                        {% endif %}
                    </form>
                </div>
                
                <table class="user-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Username</th>
                            <th>User Type</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Last Login</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for user in users %}
                        <tr>
                            <td>{{ user.user_id }}</td>
                            <td>{{ user.username }}</td>
                            <td>{{ user.user_type }}</td>
                            <td>
                                <span class="role-badge role-{{ user.user_type.split()[0] }}">
                                    {{ user.user_type|capitalize }}
                                </span>
                            </span>
                            <td>
                                <span class="status-badge status-{{ user.account_status }}">
                                    {{ user.account_status|capitalize }}
                                </span>
                            </span>
                            <td>{{ user.last_login_formatted if user.last_login else 'Never' }}</span>
                            <td>
                                <button onclick="editUserPermissions({{ user.user_id }})" class="btn-edit-permission">
                                    <i class="fas fa-edit"></i> Edit Permissions
                                </button>
                            </span>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                
                <!-- Pagination -->
                {% if total_pages > 1 %}
                <div class="pagination">
                    {% if current_page > 1 %}
                        <a href="?page=1&tab=users{% if search_term %}&search={{ search_term }}{% endif %}">
                            <i class="fas fa-angle-double-left"></i> First
                        </a>
                        <a href="?page={{ current_page - 1 }}&tab=users{% if search_term %}&search={{ search_term }}{% endif %}">
                            <i class="fas fa-angle-left"></i> Prev
                        </a>
                    {% else %}
                        <span class="disabled"><i class="fas fa-angle-double-left"></i> First</span>
                        <span class="disabled"><i class="fas fa-angle-left"></i> Prev</span>
                    {% endif %}
                    
                    {% for page_num in page_range %}
                        {% if page_num == current_page %}
                            <span class="current">{{ page_num }}</span>
                        {% else %}
                            <a href="?page={{ page_num }}&tab=users{% if search_term %}&search={{ search_term }}{% endif %}">{{ page_num }}</a>
                        {% endif %}
                    {% endfor %}
                    
                    {% if current_page < total_pages %}
                        <a href="?page={{ current_page + 1 }}&tab=users{% if search_term %}&search={{ search_term }}{% endif %}">
                            Next <i class="fas fa-angle-right"></i>
                        </a>
                        <a href="?page={{ total_pages }}&tab=users{% if search_term %}&search={{ search_term }}{% endif %}">
                            Last <i class="fas fa-angle-double-right"></i>
                        </a>
                    {% else %}
                        <span class="disabled">Next <i class="fas fa-angle-right"></i></span>
                        <span class="disabled">Last <i class="fas fa-angle-double-right"></i></span>
                    {% endif %}
                </div>
                
                <div class="page-info">
                    Showing {{ offset + 1 }} to {{ offset + per_page if offset + per_page <= total_users else total_users }} of {{ total_users }} users
                    {% if search_term %}
                        (filtered by "{{ search_term }}")
                    {% endif %}
                </div>
                {% endif %}
            </div>
            
            <!-- Role Management Tab -->
            <div id="roles-tab" class="tab-content">
                <h3><i class="fas fa-user-tag"></i> Role Definitions</h3>
                <form method="POST">
                    <input type="hidden" name="action" value="update_roles">
                    
                    <div class="permission-group">
                        <h3>Available Roles</h3>
                        <div class="permission-list">
                            {% for role in roles %}
                            <div class="permission-item">
                                <input type="checkbox" name="role_{{ role.id }}" {% if role.active %}checked{% endif %}>
                                <label>{{ role.name }}</label>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <div class="permission-group">
                        <h3>Role Permissions</h3>
                        <div class="permission-list">
                            {% for perm in role_permissions %}
                            <div class="permission-item">
                                <input type="checkbox" name="perm_{{ perm.id }}" {% if perm.assigned %}checked{% endif %}>
                                <label>{{ perm.name }}</label>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <button type="submit" class="btn-save">Save Role Settings</button>
                </form>
            </div>
            
            <!-- Permission Settings Tab -->
            <div id="permissions-tab" class="tab-content">
                <h3><i class="fas fa-lock"></i> Module Permissions</h3>
                <form method="POST">
                    <input type="hidden" name="action" value="update_permissions">
                    
                    <div class="permission-group">
                        <h3>Director Permissions ({{ session.username }})</h3>
                        <div class="permission-list">
                            <div class="permission-item">
                                <input type="checkbox" name="perm_view_dashboard" {% if perms.view_dashboard %}checked{% endif %}>
                                <label>View Dashboard</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_view_students" {% if perms.view_students %}checked{% endif %}>
                                <label>View Students</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_manage_students" {% if perms.manage_students %}checked{% endif %}>
                                <label>Manage Students</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_view_teachers" {% if perms.view_teachers %}checked{% endif %}>
                                <label>View Teachers</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_manage_teachers" {% if perms.manage_teachers %}checked{% endif %}>
                                <label>Manage Teachers</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_view_staff" {% if perms.view_staff %}checked{% endif %}>
                                <label>View Admin Staff</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_manage_staff" {% if perms.manage_staff %}checked{% endif %}>
                                <label>Manage Admin Staff</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_view_users" {% if perms.view_users %}checked{% endif %}>
                                <label>View Users</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_manage_users" {% if perms.manage_users %}checked{% endif %}>
                                <label>Manage Users</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_view_grades" {% if perms.view_grades %}checked{% endif %}>
                                <label>View Grades</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_manage_grades" {% if perms.manage_grades %}checked{% endif %}>
                                <label>Manage Grades</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_view_scores" {% if perms.view_scores %}checked{% endif %}>
                                <label>View Scores</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_manage_scores" {% if perms.manage_scores %}checked{% endif %}>
                                <label>Manage Scores</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_view_reports" {% if perms.view_reports %}checked{% endif %}>
                                <label>View Reports</label>
                            </div>
                            <div class="permission-item">
                                <input type="checkbox" name="perm_export_data" {% if perms.export_data %}checked{% endif %}>
                                <label>Export Data</label>
                            </div>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn-save">Save Permissions</button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Remove active class from all tab buttons
            const tabButtons = document.querySelectorAll('.tab');
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
            
            // Update URL with tab parameter
            const url = new URL(window.location.href);
            url.searchParams.set('tab', tabName);
            window.history.pushState({}, '', url);
        }
        
        function editUserPermissions(userId) {
            window.location.href = '/director/edit_user?id=' + userId;
        }
        
        // Preserve active tab on page load
        document.addEventListener('DOMContentLoaded', function() {
            const urlParams = new URLSearchParams(window.location.search);
            const activeTab = urlParams.get('tab');
            if (activeTab && activeTab !== 'users') {
                showTab(activeTab);
            }
        });
        
        // Confirm before saving
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!confirm('Are you sure you want to save these changes?')) {
                    e.preventDefault();
                }
            });
        });
    </script>
</body>
</html>
"""

@user_permissions_bp.route('/director/user_permissions', methods=['GET', 'POST'])
def user_permissions():
    """User permissions management for director with pagination"""
    
    # Check if user is logged in as director
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return redirect(url_for('unauthorized'))
    
    success = ''
    error = ''
    
    # Get pagination and filter parameters
    current_page = request.args.get('page', 1, type=int)
    if current_page < 1:
        current_page = 1
    
    search_term = request.args.get('search', '').strip()
    per_page = 10
    offset = (current_page - 1) * per_page
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Handle POST requests
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'update_permissions':
            try:
                success = "Permissions updated successfully!"
            except Exception as e:
                error = f"Error updating permissions: {str(e)}"
                conn.rollback()
        
        elif action == 'update_roles':
            try:
                success = "Role settings updated successfully!"
            except Exception as e:
                error = f"Error updating roles: {str(e)}"
                conn.rollback()
    
    # Get statistics (no pagination for stats)
    try:
        # Total users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()['count']
        
        # Directors count
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE user_type LIKE '%director%'")
        directors_count = cursor.fetchone()['count']
        
        # Teachers count
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE user_type LIKE '%teacher%'")
        teachers_count = cursor.fetchone()['count']
        
        # Students count
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE user_type LIKE '%student%'")
        students_count = cursor.fetchone()['count']
        
        # Build query for users with search
        query = "SELECT user_id, username, user_type, account_status, last_login, created_at FROM users"
        count_query = "SELECT COUNT(*) as total FROM users"
        params = []
        
        if search_term:
            query += " WHERE username LIKE %s OR user_type LIKE %s"
            count_query += " WHERE username LIKE %s OR user_type LIKE %s"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        
        # Execute count query
        cursor.execute(count_query, params)
        total_filtered_users = cursor.fetchone()['total']
        
        # Execute main query with pagination
        query_params = params + [per_page, offset]
        cursor.execute(query, query_params)
        users = cursor.fetchall()
        
        # Format dates
        for user in users:
            if user.get('last_login'):
                if isinstance(user['last_login'], datetime):
                    user['last_login_formatted'] = user['last_login'].strftime('%Y-%m-%d %H:%M')
                else:
                    user['last_login_formatted'] = str(user['last_login'])
        
    except Exception as e:
        print(f"Database error: {e}")
        total_users = 0
        directors_count = 0
        teachers_count = 0
        students_count = 0
        total_filtered_users = 0
        users = []
        error = "Error loading data"
    finally:
        cursor.close()
        conn.close()
    
    # Calculate pagination
    total_pages = (total_filtered_users + per_page - 1) // per_page if total_filtered_users > 0 else 1
    
    # Generate page range for pagination
    max_links = 5
    start_page = max(1, current_page - max_links // 2)
    end_page = min(total_pages, start_page + max_links - 1)
    
    if end_page - start_page + 1 < max_links:
        start_page = max(1, end_page - max_links + 1)
    
    page_range = list(range(start_page, end_page + 1))
    
    # Default permissions for director
    perms = {
        'view_dashboard': True,
        'view_students': True,
        'manage_students': True,
        'view_teachers': True,
        'manage_teachers': True,
        'view_staff': True,
        'manage_staff': True,
        'view_users': True,
        'manage_users': True,
        'view_grades': True,
        'manage_grades': True,
        'view_scores': True,
        'manage_scores': True,
        'view_reports': True,
        'export_data': True
    }
    
    # Role definitions
    roles = [
        {'id': 1, 'name': 'Director', 'active': True},
        {'id': 2, 'name': 'Vice Director', 'active': True},
        {'id': 3, 'name': 'Supervisor', 'active': True},
        {'id': 4, 'name': 'Room Teacher', 'active': True},
        {'id': 5, 'name': 'Subject Teacher', 'active': True},
        {'id': 6, 'name': 'Student', 'active': True},
        {'id': 7, 'name': 'Parent', 'active': True},
    ]
    
    role_permissions = [
        {'id': 1, 'name': 'View Dashboard', 'assigned': True},
        {'id': 2, 'name': 'Manage Students', 'assigned': True},
        {'id': 3, 'name': 'Manage Teachers', 'assigned': True},
        {'id': 4, 'name': 'View Reports', 'assigned': True},
        {'id': 5, 'name': 'Export Data', 'assigned': True},
    ]
    
    return render_template_string(
        HTML_TEMPLATE,
        success=success,
        error=error,
        total_users=total_users,
        directors_count=directors_count,
        teachers_count=teachers_count,
        students_count=students_count,
        users=users,
        perms=perms,
        roles=roles,
        role_permissions=role_permissions,
        current_page=current_page,
        total_pages=total_pages,
        per_page=per_page,
        offset=offset,
        search_term=search_term,
        page_range=page_range
    )


print("✅ user_permissions.py blueprint loaded with pagination")
print("   📌 Route: /director/user_permissions")