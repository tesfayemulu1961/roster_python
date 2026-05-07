# ==============================================
# functions.py - Shared application functions
# Python equivalent of PHP's functions.php
# ==============================================

from flask import session, url_for
from datetime import datetime
import re

# ==============================================
# Template helper functions (for Jinja2 templates)
# ==============================================

def display_header(title, user_role=None):
    """
    Generate HTML header (like PHP's displayHeader function)
    Returns HTML string for header
    """
    if user_role is None:
        user_role = session.get('user_type', 'Guest')
    
    username = session.get('username', 'User')
    
    header_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - School Management System</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f4f4; }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header h1 {{ font-size: 24px; }}
            .user-info {{ display: flex; align-items: center; gap: 15px; }}
            .logout-btn {{
                background: #dc3545;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
            }}
            .container {{ max-width: 1200px; margin: 30px auto; padding: 0 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1><i class="fas fa-school"></i> {title}</h1>
            <div class="user-info">
                <span><i class="fas fa-user"></i> {username} ({user_role})</span>
                <a href="{url_for('logout')}" class="logout-btn"><i class="fas fa-sign-out-alt"></i> Logout</a>
            </div>
        </div>
        <div class="container">
    '''
    return header_html


def display_sidebar_menu(items):
    """
    Generate HTML sidebar menu (like PHP's displaySidebarMenu function)
    items: list of menu items with 'url', 'icon', 'label', 'submenu' (optional)
    
    Example:
        items = [
            {'url': '/dashboard', 'icon': 'home', 'label': 'Dashboard'},
            {'url': '#', 'icon': 'users', 'label': 'Users', 'submenu': [
                {'url': '/users/list', 'label': 'List Users'},
                {'url': '/users/add', 'label': 'Add User'}
            ]}
        ]
    """
    menu_html = '''
    <div class="sidebar">
        <nav class="sidebar-nav">
            <ul class="nav-menu">
    '''
    
    for item in items:
        if 'submenu' in item:
            # Dropdown menu item
            menu_html += f'''
                <li class="nav-item dropdown">
                    <a href="#" class="nav-link dropdown-toggle" data-toggle="dropdown">
                        <i class="fas fa-{item['icon']}"></i> {item['label']}
                    </a>
                    <ul class="dropdown-menu">
            '''
            for subitem in item['submenu']:
                menu_html += f'<li><a href="{subitem["url"]}" class="dropdown-item">{subitem["label"]}</a></li>'
            menu_html += '''
                    </ul>
                </li>
            '''
        else:
            # Regular menu item
            menu_html += f'''
                <li class="nav-item">
                    <a href="{item['url']}" class="nav-link">
                        <i class="fas fa-{item['icon']}"></i> {item['label']}
                    </a>
                </li>
            '''
    
    menu_html += '''
            </ul>
        </nav>
    </div>
    <style>
        .sidebar {
            width: 280px;
            background: #2c3e50;
            color: white;
            position: fixed;
            left: 0;
            top: 70px;
            height: calc(100% - 70px);
            overflow-y: auto;
        }
        .nav-menu {
            list-style: none;
            padding: 20px 0;
        }
        .nav-item {
            margin-bottom: 5px;
        }
        .nav-link {
            display: block;
            padding: 12px 20px;
            color: white;
            text-decoration: none;
            transition: background 0.3s;
        }
        .nav-link:hover {
            background: #34495e;
        }
        .dropdown-menu {
            background: #34495e;
            border: none;
            padding-left: 30px;
        }
        .dropdown-item {
            padding: 8px 20px;
            color: white;
            text-decoration: none;
            display: block;
        }
        .dropdown-item:hover {
            background: #2c3e50;
        }
        .main-content {
            margin-left: 280px;
            padding: 20px;
        }
        @media (max-width: 768px) {
            .sidebar { display: none; }
            .main-content { margin-left: 0; }
        }
    </style>
    '''
    return menu_html


def display_footer():
    """
    Generate HTML footer (like PHP's displayFooter function)
    """
    current_year = datetime.now().year
    footer_html = f'''
        </div> <!-- Close container -->
        <footer style="background: #2c3e50; color: white; text-align: center; padding: 15px; margin-top: 30px;">
            <p>&copy; {current_year} School Management System. All rights reserved.</p>
            <p>Developed by: Tesfaye Mulu</p>
        </footer>
    </body>
    </html>
    '''
    return footer_html


# ==============================================
# Form helper functions
# ==============================================

def generate_csrf_token():
    """
    Generate CSRF token for forms (like PHP's CSRF protection)
    """
    import secrets
    token = secrets.token_hex(32)
    session['csrf_token'] = token
    return token


def verify_csrf_token(token):
    """
    Verify CSRF token
    """
    return token == session.get('csrf_token')


def sanitize_input(data):
    """
    Sanitize user input (like PHP's filter_input)
    """
    if data is None:
        return ''
    if isinstance(data, str):
        # Remove HTML tags and escape special characters
        import html
        return html.escape(data.strip())
    return data


def validate_email(email):
    """
    Validate email address (like PHP's filter_var($email, FILTER_VALIDATE_EMAIL))
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def format_date(date_str, format_type='display'):
    """
    Format date for display (like PHP's date() function)
    """
    if not date_str:
        return ''
    
    from datetime import datetime
    if isinstance(date_str, str):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except:
            date_obj = datetime.now()
    else:
        date_obj = date_str
    
    if format_type == 'display':
        return date_obj.strftime('%b %d, %Y')
    elif format_type == 'datetime':
        return date_obj.strftime('%Y-%m-%d %H:%M:%S')
    elif format_type == 'time':
        return date_obj.strftime('%I:%M %p')
    else:
        return date_obj.strftime('%Y-%m-%d')


# ==============================================
# Database helper functions
# ==============================================

def get_user_role_name(user_type):
    """
    Get display name for user role
    """
    role_names = {
        'director': 'Director',
        'vice director': 'Vice Director',
        'supervisor': 'Supervisor',
        'KG director': 'KG Director',
        'student': 'Student',
        'parent': 'Parent'
    }
    
    # Check for teacher roles
    if 'room teacher' in user_type.lower():
        return 'Room Teacher'
    elif 'subject teacher' in user_type.lower():
        return 'Subject Teacher'
    
    return role_names.get(user_type, user_type)


def get_grade_name(grade_id):
    """
    Get grade name from grade ID (like PHP function)
    """
    grade_map = {
        5: 'Grade 1',
        6: 'Grade 2',
        7: 'Grade 3',
        8: 'Grade 4',
        9: 'Grade 5',
        10: 'Grade 6',
        11: 'Grade 7',
        12: 'Grade 8'
    }
    return grade_map.get(grade_id, f'Grade {grade_id}')


def calculate_average(scores):
    """
    Calculate average from scores list (like PHP's array_sum/count)
    """
    if not scores:
        return 0
    valid_scores = [s for s in scores if s is not None and s > 0]
    if not valid_scores:
        return 0
    return round(sum(valid_scores) / len(valid_scores), 2)


def get_status_badge(status):
    """
    Get HTML badge for status (like PHP function)
    """
    badges = {
        'active': '<span class="badge badge-success">Active</span>',
        'inactive': '<span class="badge badge-danger">Inactive</span>',
        'suspended': '<span class="badge badge-warning">Suspended</span>',
        'promoted': '<span class="badge badge-info">Promoted</span>',
        'repeat': '<span class="badge badge-warning">Repeat</span>',
        'graduated': '<span class="badge badge-success">Graduated</span>'
    }
    return badges.get(status, f'<span class="badge badge-secondary">{status}</span>')


# ==============================================
# Flask template context processor
# ==============================================

def add_template_helpers(app):
    """
    Add helper functions to all Jinja2 templates
    Usage: call this in your app.py after creating the Flask app
    """
    @app.context_processor
    def utility_processor():
        return {
            'now': datetime.now(),
            'current_year': datetime.now().year,
            'get_user_role_name': get_user_role_name,
            'get_grade_name': get_grade_name,
            'calculate_average': calculate_average,
            'get_status_badge': get_status_badge,
            'format_date': format_date,
            'url_for': url_for
        }


# ==============================================
# Pagination helper
# ==============================================

def paginate(items, page=1, per_page=20):
    """
    Paginate a list of items (like PHP's pagination)
    """
    total = len(items)
    total_pages = (total + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }


# ==============================================
# File upload helper
# ==============================================

def allowed_file(filename, allowed_extensions={'png', 'jpg', 'jpeg', 'gif', 'pdf'}):
    """
    Check if file extension is allowed (like PHP's file validation)
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def upload_file(file, upload_folder, max_size_mb=5):
    """
    Handle file upload (like PHP's move_uploaded_file)
    """
    import os
    from werkzeug.utils import secure_filename
    
    if not file:
        return None, "No file provided"
    
    if not allowed_file(file.filename):
        return None, "File type not allowed"
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Seek back to beginning
    
    if size > max_size_mb * 1024 * 1024:
        return None, f"File too large. Max size: {max_size_mb}MB"
    
    filename = secure_filename(file.filename)
    # Add timestamp to filename to avoid duplicates
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{name}_{timestamp}{ext}"
    
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    return filename, None


# ==============================================
# Guard to prevent multiple includes (like PHP's defined check)
# ==============================================

_FUNCTIONS_LOADED = True

if __name__ == "__main__":
    # Test the functions
    print("Functions loaded successfully!")
    print(f"Current year: {datetime.now().year}")
    print(f"User role name: {get_user_role_name('director')}")
    print(f"Grade name: {get_grade_name(10)}")