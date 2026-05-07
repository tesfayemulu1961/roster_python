#!/usr/bin/env python3
"""
PHP to Python/Flask Converter - Skips specified files
"""

import os
import re
import shutil
from pathlib import Path

# Configuration
PHP_ROOT = r'C:\xampp\htdocs\roster_php'
PYTHON_ROOT = r'C:\xampp\htdocs\roster_python'

# Files to skip (do NOT convert)
SKIP_FILES = [
    'index.php',
    'login.php', 
    'auth_check.php',
    'config.php',
    'db_conn.php',
    'db_config.php',
    'functions.php',
    'director_dashboard.php'
]

# Directories to skip
SKIP_DIRS = ['vendor', 'node_modules', 'cache', 'logs', 'temp', 'uploads', 'sessions']

# Template for converted Python files
TEMPLATE = '''# ==============================================
# Python/Flask equivalent of {php_file}
# Original PHP Path: {php_path}
# ==============================================

from flask import Blueprint, jsonify, session, redirect, request
from functools import wraps
import mysql.connector
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
{blueprint_name} = Blueprint('{blueprint_name}', __name__, url_prefix='{url_prefix}')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

{page_content}

# Register this blueprint in main app
# from {blueprint_module} import {blueprint_name}
# app.register_blueprint({blueprint_name})
'''

def get_blueprint_name(relative_path, module_name):
    """Generate a unique blueprint name"""
    dir_part = os.path.dirname(relative_path)
    if dir_part:
        clean_dir = re.sub(r'[^a-zA-Z0-9_]', '_', dir_part)
        blueprint = f"{clean_dir}_{module_name}"
    else:
        blueprint = module_name
    
    if blueprint[0].isdigit():
        blueprint = f"bp_{blueprint}"
    
    return blueprint

def create_blueprint_from_php(php_path):
    """Create a Python blueprint file from a PHP file"""
    relative_path = os.path.relpath(php_path, PHP_ROOT)
    folder_path = os.path.dirname(relative_path)
    module_name = os.path.splitext(os.path.basename(php_path))[0]
    
    # Determine URL prefix
    if folder_path == '.':
        url_prefix = ''
        blueprint_name = module_name
    else:
        url_prefix = '/' + folder_path.replace('\\', '/')
        blueprint_name = get_blueprint_name(relative_path, module_name)
    
    # Extract title from PHP file
    title = module_name.replace('_', ' ').title().replace('.Php', '')
    try:
        with open(php_path, 'r', encoding='utf-8') as f:
            php_content = f.read()
            title_match = re.search(r'<title>(.*?)</title>', php_content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1)
    except:
        pass
    
    page_content = f'''
@app.route('/{module_name}')
@login_required
def {module_name}_page():
    """Page: {title} - Converted from {os.path.basename(php_path)}"""
    # TODO: Implement the specific functionality
    # Original PHP file: {php_path}
    
    return jsonify({{
        "message": "Page: {title}",
        "original_file": "{os.path.basename(php_path)}",
        "status": "under_construction"
    }})
'''
    
    content = TEMPLATE.format(
        php_file=os.path.basename(php_path),
        php_path=php_path,
        blueprint_name=blueprint_name,
        url_prefix=url_prefix,
        blueprint_module=blueprint_name,
        page_content=page_content
    )
    
    return content

def scan_and_convert():
    """Scan PHP directory and convert all PHP files except skipped ones"""
    
    print("=" * 70)
    print("PHP to Python Converter")
    print("=" * 70)
    print(f"PHP Source: {PHP_ROOT}")
    print(f"Python Target: {PYTHON_ROOT}")
    print(f"\nSkipping: {', '.join(SKIP_FILES)}")
    print("=" * 70)
    
    converted = []
    skipped = []
    errors = []
    file_count = 0
    
    # Check if PHP root exists
    if not os.path.exists(PHP_ROOT):
        print(f"\n❌ ERROR: PHP folder not found at {PHP_ROOT}")
        print("Please update PHP_ROOT in the script to the correct path.")
        return converted, errors
    
    for root, dirs, files in os.walk(PHP_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            if file.endswith('.php'):
                file_count += 1
                
                if file in SKIP_FILES:
                    skipped.append(file)
                    print(f"⏭️  Skipping: {file}")
                    continue
                
                php_path = os.path.join(root, file)
                relative_path = os.path.relpath(php_path, PHP_ROOT)
                python_file = relative_path.replace('.php', '.py')
                output_path = os.path.join(PYTHON_ROOT, python_file)
                
                try:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    content = create_blueprint_from_php(php_path)
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    converted.append(relative_path)
                    print(f"✅ Converted: {relative_path}")
                    
                except Exception as e:
                    errors.append(f"{relative_path}: {e}")
                    print(f"❌ Error: {relative_path} - {e}")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total PHP files found: {file_count}")
    print(f"Files converted: {len(converted)}")
    print(f"Files skipped: {len(skipped)}")
    print(f"Errors: {len(errors)}")
    print("=" * 70)
    
    return converted, errors

def create_main_app():
    """Create a simple main app file if it doesn't exist"""
    app_path = os.path.join(PYTHON_ROOT, 'app.py')
    
    if not os.path.exists(app_path):
        app_content = '''from flask import Flask, session, redirect
import os
import importlib

app = Flask(__name__)
app.secret_key = 'your-secret-key'

@app.route('/')
def home():
    return '<a href="/login">Go to Login</a>'

if __name__ == '__main__':
    app.run(debug=True, port=5000)
'''
        with open(app_path, 'w') as f:
            f.write(app_content)
        print(f"\n✅ Created {app_path}")

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("PHP TO PYTHON CONVERTER")
    print("=" * 70)
    
    converted, errors = scan_and_convert()
    create_main_app()
    
    print("\n✅ Conversion complete!")
    print("\nTo run your converted app:")
    print(f"  cd {PYTHON_ROOT}")
    print("  python app.py")