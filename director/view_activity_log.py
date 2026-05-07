from flask import Blueprint, request, session, redirect, url_for, render_template_string, jsonify, Response
import mysql.connector
from datetime import datetime, timedelta
import csv
import io

# Create blueprint
activity_log_bp = Blueprint('activity_log', __name__)

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
    <title>Activity Log Viewer</title>
    <style>
        :root {
            --primary-color: #3498db;
            --secondary-color: #2980b9;
            --background-color: #f9f9f9;
            --border-color: #ddd;
            --header-bg: #f1f1f1;
            --row-even: #f8f9fa;
            --row-odd: #ffffff;
            --success-color: #2ecc71;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background-color: var(--background-color);
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
        }
        
        h1 {
            text-align: center;
            margin-bottom: 20px;
            color: #2c3e50;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        h1 a {
            background-color: #6c757d;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 14px;
        }
        
        h1 a:hover {
            background-color: #5a6268;
        }
        
        .filters {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
            padding: 15px;
            background-color: var(--header-bg);
            border-radius: 6px;
        }
        
        .filter-group {
            display: flex;
            flex-direction: column;
        }
        
        .filter-group label {
            margin-bottom: 5px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .filter-group input,
        .filter-group select {
            padding: 8px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
        }
        
        .actions {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        button {
            padding: 8px 16px;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        
        button:hover {
            background-color: var(--secondary-color);
        }
        
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        
        .btn-danger {
            background-color: var(--danger-color);
        }
        
        .btn-danger:hover {
            background-color: #c0392b;
        }
        
        .table-container {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        
        th {
            background-color: var(--header-bg);
            position: sticky;
            top: 0;
            font-weight: 600;
        }
        
        tbody tr:nth-child(even) {
            background-color: var(--row-even);
        }
        
        tbody tr:nth-child(odd) {
            background-color: var(--row-odd);
        }
        
        tbody tr:hover {
            background-color: #e9f7fe;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin-top: 20px;
        }
        
        .pagination button {
            min-width: 40px;
        }
        
        .pagination-info {
            margin: 0 10px;
        }
        
        .log-details {
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .log-details.expanded {
            white-space: normal;
            overflow: visible;
        }
        
        .expand-btn {
            background: none;
            border: none;
            color: var(--primary-color);
            cursor: pointer;
            padding: 0 5px;
            font-size: 0.9rem;
        }
        
        .no-results {
            text-align: center;
            padding: 20px;
            font-style: italic;
            color: #777;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #777;
        }
        
        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .status-LOGIN {
            background-color: var(--success-color);
            color: white;
        }
        
        .status-LOGOUT {
            background-color: var(--warning-color);
            color: white;
        }
        
        .status-LOGIN_FAILED {
            background-color: var(--danger-color);
            color: white;
        }
        
        @media (max-width: 768px) {
            .filters {
                grid-template-columns: 1fr;
            }
            
            th, td {
                padding: 8px 10px;
                font-size: 0.9rem;
            }
            
            .container {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>
            <i class="fas fa-history"></i> Activity Log Viewer
            <a href="/director/director_dashboard">Back to Dashboard</a>
        </h1>
        
        <div class="filters">
            <div class="filter-group">
                <label for="user-id">User ID</label>
                <input type="number" id="user-id" min="1">
            </div>
            
            <div class="filter-group">
                <label for="username">Username</label>
                <input type="text" id="username">
            </div>
            
            <div class="filter-group">
                <label for="user-type">User Type</label>
                <select id="user-type">
                    <option value="">All Types</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label for="action">Action</label>
                <select id="action">
                    <option value="">All Actions</option>
                    <option value="LOGIN">Login</option>
                    <option value="LOGOUT">Logout</option>
                    <option value="LOGIN_FAILED">Login Failed</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label for="date-from">Date From</label>
                <input type="date" id="date-from">
            </div>
            
            <div class="filter-group">
                <label for="date-to">Date To</label>
                <input type="date" id="date-to">
            </div>
        </div>
        
        <div class="actions">
            <button id="apply-filters">Apply Filters</button>
            <button id="export-csv">Export to CSV</button>
            <button id="refresh-data">Refresh Data</button>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Log ID</th>
                        <th>User ID</th>
                        <th>Username</th>
                        <th>User Type</th>
                        <th>Action</th>
                        <th>Details</th>
                        <th>IP Address</th>
                        <th>User Agent</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody id="log-entries">
                    <tr>
                        <td colspan="9" class="loading">Loading activity logs...</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="no-results" id="no-results" style="display: none;">
            No activity log entries found matching your filters.
        </div>
        
        <div class="pagination">
            <button id="first-page" disabled>First</button>
            <button id="prev-page" disabled>Previous</button>
            <span class="pagination-info" id="page-info">Page 1 of 1</span>
            <button id="next-page" disabled>Next</button>
            <button id="last-page" disabled>Last</button>
        </div>
    </div>

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        let currentPage = 1;
        const itemsPerPage = 10;
        let allLogs = [];
        let filteredLogs = [];
        
        const logEntries = document.getElementById('log-entries');
        const pageInfo = document.getElementById('page-info');
        const noResults = document.getElementById('no-results');
        const userTypeFilter = document.getElementById('user-type');
        const applyFiltersBtn = document.getElementById('apply-filters');
        const exportCsvBtn = document.getElementById('export-csv');
        const refreshDataBtn = document.getElementById('refresh-data');
        const firstPageBtn = document.getElementById('first-page');
        const prevPageBtn = document.getElementById('prev-page');
        const nextPageBtn = document.getElementById('next-page');
        const lastPageBtn = document.getElementById('last-page');
        
        function formatDateTime(dateTimeStr) {
            if (!dateTimeStr) return 'N/A';
            const date = new Date(dateTimeStr);
            return date.toLocaleString();
        }
        
        function renderTable() {
            logEntries.innerHTML = '';
            
            if (filteredLogs.length === 0) {
                noResults.style.display = 'block';
                return;
            }
            
            noResults.style.display = 'none';
            
            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = Math.min(startIndex + itemsPerPage, filteredLogs.length);
            const pageLogs = filteredLogs.slice(startIndex, endIndex);
            
            pageLogs.forEach(log => {
                const row = document.createElement('tr');
                
                let statusClass = '';
                if (log.action === 'LOGIN') statusClass = 'status-LOGIN';
                else if (log.action === 'LOGOUT') statusClass = 'status-LOGOUT';
                else if (log.action === 'LOGIN_FAILED') statusClass = 'status-LOGIN_FAILED';
                
                const detailsText = log.details || '';
                const hasLongDetails = detailsText.length > 50;
                
                row.innerHTML = `
                    <td>${log.log_id}</td>
                    <td>${log.user_id || 'N/A'}</td>
                    <td>${log.username || 'N/A'}</td>
                    <td>${log.user_type || 'N/A'}</td>
                    <td><span class="status-badge ${statusClass}">${log.action}</span></td>
                    <td class="log-details">
                        <span>${escapeHtml(detailsText.substring(0, 100))}</span>
                        ${hasLongDetails ? '<button class="expand-btn" onclick="toggleExpand(this)">[...]</button>' : ''}
                    </td>
                    <td>${log.ip_address || 'N/A'}</td>
                    <td title="${escapeHtml(log.user_agent || '')}">${log.user_agent ? escapeHtml(log.user_agent.substring(0, 20)) + '...' : 'N/A'}</td>
                    <td>${formatDateTime(log.created_at)}</td>
                `;
                
                logEntries.appendChild(row);
            });
            
            updatePagination();
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function updatePagination() {
            const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);
            pageInfo.textContent = `Page ${currentPage} of ${totalPages || 1}`;
            
            firstPageBtn.disabled = currentPage === 1 || filteredLogs.length === 0;
            prevPageBtn.disabled = currentPage === 1 || filteredLogs.length === 0;
            nextPageBtn.disabled = currentPage === totalPages || totalPages === 0 || filteredLogs.length === 0;
            lastPageBtn.disabled = currentPage === totalPages || totalPages === 0 || filteredLogs.length === 0;
        }
        
        window.toggleExpand = function(btn) {
            const detailsCell = btn.parentElement;
            detailsCell.classList.toggle('expanded');
            btn.textContent = detailsCell.classList.contains('expanded') ? '[Collapse]' : '[...]';
        };
        
        async function fetchData() {
            try {
                logEntries.innerHTML = '<tr><td colspan="9" class="loading">Loading activity logs...</td></tr>';
                
                const params = new URLSearchParams();
                const userId = document.getElementById('user-id').value;
                const username = document.getElementById('username').value;
                const userType = document.getElementById('user-type').value;
                const action = document.getElementById('action').value;
                const dateFrom = document.getElementById('date-from').value;
                const dateTo = document.getElementById('date-to').value;
                
                if (userId) params.append('user_id', userId);
                if (username) params.append('username', username);
                if (userType) params.append('user_type', userType);
                if (action) params.append('action', action);
                if (dateFrom) params.append('date_from', dateFrom);
                if (dateTo) params.append('date_to', dateTo);
                
                const response = await fetch(`/get_activity_logs?${params.toString()}`);
                const data = await response.json();
                
                if (data.success) {
                    allLogs = data.logs || [];
                    filteredLogs = [...allLogs];
                    
                    // Populate user type filter
                    const userTypes = [...new Set(allLogs.map(log => log.user_type).filter(t => t))];
                    while (userTypeFilter.options.length > 1) {
                        userTypeFilter.remove(1);
                    }
                    userTypes.forEach(type => {
                        const option = document.createElement('option');
                        option.value = type;
                        option.textContent = type;
                        userTypeFilter.appendChild(option);
                    });
                    
                    currentPage = 1;
                    renderTable();
                } else {
                    throw new Error(data.message || 'Failed to fetch logs');
                }
            } catch (error) {
                console.error('Error fetching activity logs:', error);
                logEntries.innerHTML = `<tr><td colspan="9" class="no-results">Error loading activity logs: ${error.message}</td></tr>`;
            }
        }
        
        function applyFilters() {
            const userId = document.getElementById('user-id').value;
            const username = document.getElementById('username').value;
            const userType = document.getElementById('user-type').value;
            const action = document.getElementById('action').value;
            const dateFrom = document.getElementById('date-from').value;
            const dateTo = document.getElementById('date-to').value;
            
            filteredLogs = allLogs.filter(log => {
                if (userId && log.user_id != userId) return false;
                if (username && !log.username?.toLowerCase().includes(username.toLowerCase())) return false;
                if (userType && log.user_type !== userType) return false;
                if (action && log.action !== action) return false;
                if (dateFrom && new Date(log.created_at) < new Date(dateFrom)) return false;
                if (dateTo && new Date(log.created_at) > new Date(dateTo + 'T23:59:59')) return false;
                return true;
            });
            
            currentPage = 1;
            renderTable();
        }
        
        function exportToCSV() {
            if (filteredLogs.length === 0) {
                alert('No data to export');
                return;
            }
            
            const params = new URLSearchParams();
            const userId = document.getElementById('user-id').value;
            const username = document.getElementById('username').value;
            const userType = document.getElementById('user-type').value;
            const action = document.getElementById('action').value;
            const dateFrom = document.getElementById('date-from').value;
            const dateTo = document.getElementById('date-to').value;
            
            if (userId) params.append('user_id', userId);
            if (username) params.append('username', username);
            if (userType) params.append('user_type', userType);
            if (action) params.append('action', action);
            if (dateFrom) params.append('date_from', dateFrom);
            if (dateTo) params.append('date_to', dateTo);
            
            window.location.href = `/export_activity_logs_csv?${params.toString()}`;
        }
        
        applyFiltersBtn.addEventListener('click', applyFilters);
        exportCsvBtn.addEventListener('click', exportToCSV);
        refreshDataBtn.addEventListener('click', fetchData);
        
        firstPageBtn.addEventListener('click', () => {
            currentPage = 1;
            renderTable();
        });
        
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderTable();
            }
        });
        
        nextPageBtn.addEventListener('click', () => {
            const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                renderTable();
            }
        });
        
        lastPageBtn.addEventListener('click', () => {
            currentPage = Math.ceil(filteredLogs.length / itemsPerPage);
            renderTable();
        });
        
        fetchData();
    });
    </script>
</body>
</html>
"""

@activity_log_bp.route('/director/activity_log', methods=['GET'])
@activity_log_bp.route('/director/view_activity_log', methods=['GET'])
def activity_log():
    """Activity log viewer page"""
    
    # Check if user is logged in as director
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return redirect(url_for('unauthorized'))
    
    return render_template_string(HTML_TEMPLATE)


@activity_log_bp.route('/get_activity_logs', methods=['GET'])
def get_activity_logs():
    """API endpoint to get activity logs with filters"""
    
    # Check if user is logged in as director
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Get filter parameters
    user_id = request.args.get('user_id')
    username = request.args.get('username')
    user_type = request.args.get('user_type')
    action = request.args.get('action')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Build query
        query = """
            SELECT al.*, u.username, u.user_type 
            FROM activity_log al
            LEFT JOIN users u ON al.user_id = u.user_id
            WHERE 1=1
        """
        params = []
        
        if user_id:
            query += " AND al.user_id = %s"
            params.append(user_id)
        
        if username:
            query += " AND u.username LIKE %s"
            params.append(f"%{username}%")
        
        if user_type:
            query += " AND u.user_type LIKE %s"
            params.append(f"%{user_type}%")
        
        if action:
            query += " AND al.action = %s"
            params.append(action)
        
        if date_from:
            query += " AND DATE(al.created_at) >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND DATE(al.created_at) <= %s"
            params.append(date_to)
        
        query += " ORDER BY al.created_at DESC LIMIT 1000"
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        
        return jsonify({'success': True, 'logs': logs})
        
    except Exception as e:
        print(f"Error fetching activity logs: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@activity_log_bp.route('/export_activity_logs_csv', methods=['GET'])
def export_activity_logs_csv():
    """Export activity logs to CSV"""
    
    # Check if user is logged in as director
    if not session.get('logged_in') or session.get('user_type') != 'director':
        return redirect(url_for('unauthorized'))
    
    # Get filter parameters
    user_id = request.args.get('user_id')
    username = request.args.get('username')
    user_type = request.args.get('user_type')
    action = request.args.get('action')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Build query
        query = """
            SELECT al.log_id, al.user_id, u.username, u.user_type, al.action, 
                   al.details, al.ip_address, al.user_agent, al.created_at
            FROM activity_log al
            LEFT JOIN users u ON al.user_id = u.user_id
            WHERE 1=1
        """
        params = []
        
        if user_id:
            query += " AND al.user_id = %s"
            params.append(user_id)
        
        if username:
            query += " AND u.username LIKE %s"
            params.append(f"%{username}%")
        
        if user_type:
            query += " AND u.user_type LIKE %s"
            params.append(f"%{user_type}%")
        
        if action:
            query += " AND al.action = %s"
            params.append(action)
        
        if date_from:
            query += " AND DATE(al.created_at) >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND DATE(al.created_at) <= %s"
            params.append(date_to)
        
        query += " ORDER BY al.created_at DESC"
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Log ID', 'User ID', 'Username', 'User Type', 'Action', 
                        'Details', 'IP Address', 'User Agent', 'Timestamp'])
        
        # Write data rows
        for log in logs:
            writer.writerow([
                log.get('log_id', ''),
                log.get('user_id', ''),
                log.get('username', ''),
                log.get('user_type', ''),
                log.get('action', ''),
                log.get('details', ''),
                log.get('ip_address', ''),
                log.get('user_agent', ''),
                log.get('created_at', '')
            ])
        
        # Prepare response
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'activity_logs_{timestamp}.csv'
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        print(f"Error exporting activity logs: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Function to log activity (to be used by other blueprints)
def log_activity(user_id, action, details=None, ip_address=None, user_agent=None):
    """Helper function to log user activity"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO activity_log (user_id, action, details, ip_address, user_agent, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (user_id, action, details, ip_address, user_agent))
        conn.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")
    finally:
        cursor.close()
        conn.close()


print("✅ activity_log.py blueprint loaded")
print("   📌 Routes:")
print("      - /director/activity_log")
print("      - /get_activity_logs (API)")
print("      - /export_activity_logs_csv (Export)")