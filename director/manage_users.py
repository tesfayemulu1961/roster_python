from flask import Blueprint, request, session, redirect, url_for, render_template_string
import mysql.connector
from datetime import datetime

# Create blueprint
manage_users_bp = Blueprint('manage_users', __name__)

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
    <title>Manage Users</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
        }
        .search-container {
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .search-box {
            display: flex;
            gap: 10px;
        }
        .search-box input[type="text"] {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 300px;
        }
        .search-box button {
            padding: 8px 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .btn {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 14px;
            cursor: pointer;
            border: none;
        }
        .btn-add {
            background-color: #4CAF50;
            color: white;
        }
        .btn-edit {
            background-color: #2196F3;
            color: white;
        }
        .btn-reset {
            background-color: #FF9800;
            color: white;
        }
        .btn-delete {
            background-color: #f44336;
            color: white;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            overflow-x: auto;
            display: block;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
            font-weight: 600;
        }
        tr:hover {
            background-color: #f9f9f9;
        }
        .status-active {
            color: green;
            font-weight: bold;
        }
        .status-inactive {
            color: orange;
            font-weight: bold;
        }
        .status-suspended {
            color: red;
            font-weight: bold;
        }
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
            color: #333;
            border-radius: 4px;
        }
        .pagination a:hover {
            background-color: #f2f2f2;
        }
        .pagination .current {
            background-color: #4CAF50;
            color: white;
            border-color: #4CAF50;
        }
        .pagination .disabled {
            color: #ccc;
            pointer-events: none;
        }
        .page-info {
            text-align: center;
            margin-top: 10px;
            color: #666;
        }
        .action-buttons {
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
        }
        @media (max-width: 768px) {
            .search-container {
                flex-direction: column;
                align-items: stretch;
            }
            .search-box {
                width: 100%;
            }
            .search-box input[type="text"] {
                flex: 1;
            }
            .action-buttons {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Manage User Accounts</h1>
        
        <div class="search-container">
            <form method="get" class="search-box">
                <input type="text" name="search" placeholder="Search users by username, type or status..." value="{{ search_term }}">
                <button type="submit">Search</button>
                {% if search_term %}
                    <a href="/director/manage_users" class="btn btn-edit">Clear</a>
                {% endif %}
            </form>
            <a href="/director/insert_users" class="btn btn-add">+ Add New User</a>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>User Type</th>
                    <th>Reference ID</th>
                    <th>Status</th>
                    <th>Last Login</th>
                    <th>Created At</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% if users %}
                    {% for user in users %}
                        <tr>
                            <td>{{ user.user_id }}</td>
                            <td>{{ user.username }}</td>
                            <td>{{ user.user_type }}</td>
                            <td>{{ user.reference_id }}</td>
                            <td class="status-{{ user.account_status }}">{{ user.account_status|capitalize }}</td>
                            <td>{{ user.last_login_formatted if user.last_login else 'Never' }}</td>
                            <td>{{ user.created_at_formatted }}</td>
                            <td class="action-buttons">
                                <a href="/director/edit_user?id={{ user.user_id }}" class="btn btn-edit">Edit</a>
                                <a href="/director/reset_password?username={{ user.username }}" class="btn btn-reset">Reset Password</a>
                                <a href="/director/manage_users?delete={{ user.user_id }}" class="btn btn-delete" onclick="return confirm('Are you sure you want to delete this user?')">Delete</a>
                            </td>
                        </tr>
                    {% endfor %}
                {% else %}
                    <tr>
                        <td colspan="8" style="text-align: center;">No users found{% if search_term %} matching your search{% endif %}</td>
                    </tr>
                {% endif %}
            </tbody>
        </table>

        {% if total_pages > 1 %}
            <div class="pagination">
                {% if current_page > 1 %}
                    <a href="?page=1{% if search_term %}&search={{ search_term }}{% endif %}">&laquo; First</a>
                    <a href="?page={{ current_page - 1 }}{% if search_term %}&search={{ search_term }}{% endif %}">&lsaquo; Prev</a>
                {% else %}
                    <span class="disabled">&laquo; First</span>
                    <span class="disabled">&lsaquo; Prev</span>
                {% endif %}

                {% for page_num in page_range %}
                    {% if page_num == current_page %}
                        <span class="current">{{ page_num }}</span>
                    {% else %}
                        <a href="?page={{ page_num }}{% if search_term %}&search={{ search_term }}{% endif %}">{{ page_num }}</a>
                    {% endif %}
                {% endfor %}

                {% if current_page < total_pages %}
                    <a href="?page={{ current_page + 1 }}{% if search_term %}&search={{ search_term }}{% endif %}">Next &rsaquo;</a>
                    <a href="?page={{ total_pages }}{% if search_term %}&search={{ search_term }}{% endif %}">Last &raquo;</a>
                {% else %}
                    <span class="disabled">Next &rsaquo;</span>
                    <span class="disabled">Last &raquo;</span>
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
</body>
</html>
"""

@manage_users_bp.route('/director/manage_users', methods=['GET'])
def manage_users():
    """Manage user accounts with pagination and search"""
    
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
        return redirect(url_for('manage_users.manage_users'))
    
    # Pagination settings
    per_page = 10
    current_page = request.args.get('page', 1, type=int)
    if current_page < 1:
        current_page = 1
    offset = (current_page - 1) * per_page
    
    # Search functionality
    search_term = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Build search condition
        if search_term:
            search_pattern = f"%{search_term}%"
            # Get total number of users for pagination
            cursor.execute("""
                SELECT COUNT(*) as total FROM users 
                WHERE username LIKE %s OR user_type LIKE %s OR account_status LIKE %s
            """, (search_pattern, search_pattern, search_pattern))
            total_users = cursor.fetchone()['total']
            
            # Get users for current page
            cursor.execute("""
                SELECT * FROM users 
                WHERE username LIKE %s OR user_type LIKE %s OR account_status LIKE %s
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, (search_pattern, search_pattern, search_pattern, per_page, offset))
        else:
            # Get total number of users for pagination
            cursor.execute("SELECT COUNT(*) as total FROM users")
            total_users = cursor.fetchone()['total']
            
            # Get users for current page
            cursor.execute("""
                SELECT * FROM users 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, (per_page, offset))
        
        users = cursor.fetchall()
        
        # Format dates for display
        for user in users:
            if user.get('last_login'):
                if isinstance(user['last_login'], datetime):
                    user['last_login_formatted'] = user['last_login'].strftime('%Y-%m-%d %H:%M')
                else:
                    user['last_login_formatted'] = str(user['last_login'])[:16]
            else:
                user['last_login_formatted'] = None
            
            if user.get('created_at'):
                if isinstance(user['created_at'], datetime):
                    user['created_at_formatted'] = user['created_at'].strftime('%Y-%m-%d %H:%M')
                else:
                    user['created_at_formatted'] = str(user['created_at'])[:16]
        
    except Exception as e:
        print(f"Database error: {e}")
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
    
    # Adjust if we're at the end
    if end_page - start_page + 1 < max_links:
        start_page = max(1, end_page - max_links + 1)
    
    page_range = list(range(start_page, end_page + 1))
    
    return render_template_string(
        HTML_TEMPLATE,
        users=users,
        total_users=total_users,
        current_page=current_page,
        total_pages=total_pages,
        per_page=per_page,
        offset=offset,
        search_term=search_term,
        page_range=page_range
    )


@manage_users_bp.route('/director/edit_user', methods=['GET', 'POST'])
def edit_user():
    """Edit user account"""
    
    # Check if user is logged in as director
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return redirect(url_for('unauthorized'))
    
    user_id = request.args.get('id', type=int)
    if not user_id:
        return redirect(url_for('manage_users.manage_users'))
    
    error = ''
    success = ''
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Update user
        user_type = request.form.get('user_type', '')
        reference_id = request.form.get('reference_id', '')
        account_status = request.form.get('account_status', 'active')
        
        try:
            cursor.execute("""
                UPDATE users 
                SET user_type = %s, reference_id = %s, account_status = %s 
                WHERE user_id = %s
            """, (user_type, reference_id, account_status, user_id))
            conn.commit()
            success = "User updated successfully!"
        except Exception as e:
            error = f"Error updating user: {str(e)}"
            conn.rollback()
    
    # Get user data
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        return "User not found", 404
    
    edit_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit User</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f5f5f5; }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            .error { color: red; background: #ffebee; padding: 10px; border-radius: 4px; margin-bottom: 15px; }
            .success { color: green; background: #e8f5e9; padding: 10px; border-radius: 4px; margin-bottom: 15px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Edit User: {{ user.username }}</h1>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            {% if success %}<div class="success">{{ success }}</div>{% endif %}
            <form method="POST">
                <div class="form-group">
                    <label>Username:</label>
                    <input type="text" value="{{ user.username }}" readonly disabled>
                </div>
                
                <div class="form-group">
                    <label>User Type:</label>
                    <input type="text" name="user_type" value="{{ user.user_type }}" required>
                </div>
                
                <div class="form-group">
                    <label>Reference ID:</label>
                    <input type="number" name="reference_id" value="{{ user.reference_id }}" required>
                </div>
                
                <div class="form-group">
                    <label>Account Status:</label>
                    <select name="account_status">
                        <option value="active" {{ 'selected' if user.account_status == 'active' }}>Active</option>
                        <option value="inactive" {{ 'selected' if user.account_status == 'inactive' }}>Inactive</option>
                        <option value="suspended" {{ 'selected' if user.account_status == 'suspended' }}>Suspended</option>
                    </select>
                </div>
                
                <button type="submit">Update User</button>
                <a href="/director/manage_users" style="margin-left: 10px;">Cancel</a>
            </form>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(edit_template, user=user, error=error, success=success)


@manage_users_bp.route('/director/reset_password', methods=['GET', 'POST'])
def reset_password():
    """Reset user password"""
    
    # Check if user is logged in as director
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return redirect(url_for('unauthorized'))
    
    from werkzeug.security import generate_password_hash
    
    username = request.args.get('username')
    if not username:
        return redirect(url_for('manage_users.manage_users'))
    
    error = ''
    success = ''
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get user data
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    if not user:
        cursor.close()
        conn.close()
        return "User not found", 404
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not new_password:
            error = "Password is required"
        elif len(new_password) < 4:
            error = "Password must be at least 4 characters"
        elif new_password != confirm_password:
            error = "Passwords do not match"
        else:
            try:
                password_hash = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password_hash = %s WHERE username = %s", (password_hash, username))
                conn.commit()
                success = "Password reset successfully!"
            except Exception as e:
                error = f"Error resetting password: {str(e)}"
                conn.rollback()
    
    cursor.close()
    conn.close()
    
    reset_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Password</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f5f5f5; }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #FF9800; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            .error { color: red; background: #ffebee; padding: 10px; border-radius: 4px; margin-bottom: 15px; }
            .success { color: green; background: #e8f5e9; padding: 10px; border-radius: 4px; margin-bottom: 15px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Reset Password for: {{ user.username }}</h1>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            {% if success %}<div class="success">{{ success }}</div>{% endif %}
            <form method="POST">
                <div class="form-group">
                    <label>New Password:</label>
                    <input type="password" name="new_password" required>
                </div>
                <div class="form-group">
                    <label>Confirm Password:</label>
                    <input type="password" name="confirm_password" required>
                </div>
                <button type="submit">Reset Password</button>
                <a href="/director/manage_users" style="margin-left: 10px;">Cancel</a>
            </form>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(reset_template, user=user, error=error, success=success)


print("✅ manage_users.py blueprint loaded")
print("   📌 Routes:")
print("      - /director/manage_users")
print("      - /director/edit_user")
print("      - /director/reset_password")