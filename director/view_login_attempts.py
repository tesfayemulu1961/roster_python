from flask import Blueprint, jsonify, session, redirect, request, render_template_string
from functools import wraps
import mysql.connector
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint - USE THIS, not @app.route
view_login_attempts_bp = Blueprint('view_login_attempts', __name__, url_prefix='/director')

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db():
    return mysql.connector.connect(**db_config)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# HTML Template for the page
LOGIN_ATTEMPTS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Attempts Report</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h2 {
            color: #333;
            margin-bottom: 20px;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        
        .filter-form {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: flex-end;
        }
        
        .filter-group {
            display: flex;
            flex-direction: column;
        }
        
        .filter-group label {
            font-size: 12px;
            margin-bottom: 5px;
            color: #666;
        }
        
        .filter-group input, .filter-group select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        
        button {
            padding: 8px 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        
        button:hover {
            background-color: #45a049;
        }
        
        .reset-btn {
            background-color: #666;
        }
        
        .reset-btn:hover {
            background-color: #555;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background-color: #4CAF50;
            color: white;
            font-weight: 600;
        }
        
        tr:hover {
            background-color: #f5f5f5;
        }
        
        .login-success {
            background-color: #d4edda;
        }
        
        .login-failed {
            background-color: #f8d7da;
        }
        
        .logout {
            background-color: #fff3cd;
        }
        
        .badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
        }
        
        .badge-success {
            background-color: #28a745;
            color: white;
        }
        
        .badge-danger {
            background-color: #dc3545;
            color: white;
        }
        
        .badge-warning {
            background-color: #ffc107;
            color: #333;
        }
        
        .no-results {
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }
        
        .stats {
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 5px;
            flex: 1;
            min-width: 150px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .stat-card h3 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .stat-card p {
            color: #666;
            font-size: 12px;
        }
        
        .stat-card.success h3 { color: #28a745; }
        .stat-card.danger h3 { color: #dc3545; }
        .stat-card.warning h3 { color: #ffc107; }
        
        @media (max-width: 768px) {
            .filter-form {
                flex-direction: column;
            }
            .filter-group {
                width: 100%;
            }
            .stats {
                flex-direction: column;
            }
            th, td {
                padding: 8px;
                font-size: 12px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>🔐 Login Attempts Report</h2>
        
        <div class="stats" id="stats">
            <div class="stat-card success">
                <h3 id="login-count">0</h3>
                <p>Successful Logins</p>
            </div>
            <div class="stat-card danger">
                <h3 id="failed-count">0</h3>
                <p>Failed Attempts</p>
            </div>
            <div class="stat-card warning">
                <h3 id="logout-count">0</h3>
                <p>Logouts</p>
            </div>
        </div>
        
        <form method="GET" class="filter-form">
            <div class="filter-group">
                <label>Username</label>
                <input type="text" name="username" placeholder="Username" value="{{ username }}">
            </div>
            <div class="filter-group">
                <label>Action</label>
                <select name="action">
                    <option value="">All Actions</option>
                    <option value="LOGIN" {{ 'selected' if action == 'LOGIN' else '' }}>Login</option>
                    <option value="LOGIN_FAILED" {{ 'selected' if action == 'LOGIN_FAILED' else '' }}>Login Failed</option>
                    <option value="LOGOUT" {{ 'selected' if action == 'LOGOUT' else '' }}>Logout</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Date</label>
                <input type="date" name="date" value="{{ date }}">
            </div>
            <div class="filter-group">
                <label>&nbsp;</label>
                <button type="submit">🔍 Filter</button>
            </div>
            <div class="filter-group">
                <label>&nbsp;</label>
                <button type="button" class="reset-btn" onclick="window.location.href='/director/view_login_attempts'">🔄 Reset</button>
            </div>
        </form>
        
        <div style="overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Username</th>
                        <th>Action</th>
                        <th>Details</th>
                        <th>IP Address</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in logs %}
                    <tr class="{{ 'login-success' if log.action == 'LOGIN' else 'login-failed' if log.action == 'LOGIN_FAILED' else 'logout' }}">
                        <td>{{ log.created_at }}</td>
                        <td>{{ log.username }}</td>
                        <td>
                            {% if log.action == 'LOGIN' %}
                                <span class="badge badge-success">✅ LOGIN</span>
                            {% elif log.action == 'LOGIN_FAILED' %}
                                <span class="badge badge-danger">❌ LOGIN FAILED</span>
                            {% else %}
                                <span class="badge badge-warning">🚪 LOGOUT</span>
                            {% endif %}
                        </span>
                        <td>{{ log.details or '' }}</span>
                        <td>{{ log.ip_address or 'N/A' }}</span>
                    </span>
                    {% endfor %}
                </tbody>
             </span>
        </div>
        
        {% if not logs %}
        <div class="no-results">
            <p>📭 No login attempts found.</p>
        </div>
        {% endif %}
    </div>
    
    <script>
        // Update statistics
        const logs = {{ logs|tojson }};
        const loginCount = logs.filter(l => l.action === 'LOGIN').length;
        const failedCount = logs.filter(l => l.action === 'LOGIN_FAILED').length;
        const logoutCount = logs.filter(l => l.action === 'LOGOUT').length;
        
        document.getElementById('login-count').textContent = loginCount;
        document.getElementById('failed-count').textContent = failedCount;
        document.getElementById('logout-count').textContent = logoutCount;
    </script>
</body>
</html>
'''

# USE BLUEPRINT ROUTE DECORATOR, NOT @app.route
@view_login_attempts_bp.route('/view_login_attempts')
@login_required
def view_login_attempts():
    """Display login attempts report"""
    try:
        # Get filter parameters
        filter_username = request.args.get('username', '').strip()
        filter_action = request.args.get('action', '').strip()
        filter_date = request.args.get('date', '').strip()
        
        # Build query
        query = """
            SELECT log_id, created_at, username, action, details, ip_address, user_agent
            FROM activity_log 
            WHERE action IN ('LOGIN', 'LOGIN_FAILED', 'LOGOUT')
        """
        params = []
        
        if filter_username:
            query += " AND username LIKE %s"
            params.append(f'%{filter_username}%')
        
        if filter_action:
            query += " AND action = %s"
            params.append(filter_action)
        
        if filter_date:
            query += " AND DATE(created_at) = %s"
            params.append(filter_date)
        
        query += " ORDER BY created_at DESC LIMIT 50"
        
        # Execute query
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Format results
        logs = []
        for row in rows:
            logs.append({
                'log_id': row[0],
                'created_at': row[1].strftime('%Y-%m-%d %H:%M:%S') if row[1] else '',
                'username': row[2] if row[2] else 'N/A',
                'action': row[3],
                'details': row[4] if row[4] else '',
                'ip_address': row[5] if row[5] else 'N/A',
                'user_agent': row[6] if row[6] else ''
            })
        
        cursor.close()
        conn.close()
        
        # Render template with data
        return render_template_string(
            LOGIN_ATTEMPTS_TEMPLATE,
            logs=logs,
            username=filter_username,
            action=filter_action,
            date=filter_date
        )
        
    except Exception as e:
        print(f"Error in view_login_attempts: {str(e)}")
        return f"<h1>Error</h1><p>{str(e)}</p>", 500


# API endpoint to get JSON data
@view_login_attempts_bp.route('/api/login_attempts')
@login_required
def api_login_attempts():
    """Return login attempts as JSON"""
    try:
        filter_username = request.args.get('username', '').strip()
        filter_action = request.args.get('action', '').strip()
        filter_date = request.args.get('date', '').strip()
        
        query = """
            SELECT log_id, created_at, username, action, details, ip_address, user_agent
            FROM activity_log 
            WHERE action IN ('LOGIN', 'LOGIN_FAILED', 'LOGOUT')
        """
        params = []
        
        if filter_username:
            query += " AND username LIKE %s"
            params.append(f'%{filter_username}%')
        
        if filter_action:
            query += " AND action = %s"
            params.append(filter_action)
        
        if filter_date:
            query += " AND DATE(created_at) = %s"
            params.append(filter_date)
        
        query += " ORDER BY created_at DESC LIMIT 50"
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        logs = []
        for row in rows:
            logs.append({
                'log_id': row[0],
                'created_at': row[1].strftime('%Y-%m-%d %H:%M:%S') if row[1] else '',
                'username': row[2] if row[2] else 'N/A',
                'action': row[3],
                'details': row[4] if row[4] else '',
                'ip_address': row[5] if row[5] else 'N/A',
                'user_agent': row[6] if row[6] else ''
            })
        
        cursor.close()
        conn.close()
        
        # Calculate statistics
        login_count = sum(1 for log in logs if log['action'] == 'LOGIN')
        failed_count = sum(1 for log in logs if log['action'] == 'LOGIN_FAILED')
        logout_count = sum(1 for log in logs if log['action'] == 'LOGOUT')
        
        return jsonify({
            'success': True,
            'logs': logs,
            'stats': {
                'login': login_count,
                'failed': failed_count,
                'logout': logout_count,
                'total': len(logs)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500