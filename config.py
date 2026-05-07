# ==============================================
# CONFIGURATION FILE - Python version
# ==============================================

import os
import logging
from datetime import timedelta
from pathlib import Path

# ==============================================
# APPLICATION PATHS
# ==============================================
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / 'logs'
SESSIONS_DIR = BASE_DIR / 'sessions'

# Create directories if they don't exist
LOGS_DIR.mkdir(exist_ok=True, mode=0o700)
SESSIONS_DIR.mkdir(exist_ok=True, mode=0o700)

# ==============================================
# ERROR REPORTING & LOGGING CONFIGURATION
# ==============================================
# Configure logging (equivalent to PHP error_log)
logging.basicConfig(
    level=logging.DEBUG if os.getenv('ENVIRONMENT', 'development') == 'development' else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'app_errors.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger(__name__)

# ==============================================
# DATABASE CONFIGURATION
# ==============================================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'roster'),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
    'autocommit': False,
    'use_pure': True,
    'pool_name': 'roster_pool',
    'pool_size': 5
}

# Connection string for SQLAlchemy (if used)
DATABASE_URL = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"

# PDO-style configuration (for compatibility with PHP mindset)
DB_DSN = f"mysql:host={DB_CONFIG['host']};dbname={DB_CONFIG['database']};charset={DB_CONFIG['charset']}"

# ==============================================
# APPLICATION SETTINGS
# ==============================================
APP_NAME = os.getenv('APP_NAME', 'Ethio School Management')
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')  # 'development' or 'production'
DEBUG_MODE = ENVIRONMENT == 'development'

# ==============================================
# SESSION CONFIGURATION (Flask equivalent)
# ==============================================
SESSION_CONFIG = {
    'SESSION_COOKIE_NAME': 'SCHOOL_SYSTEM_SESSID',
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SECURE': False,  # Set to True if using HTTPS
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': timedelta(days=1),  # 86400 seconds
    'SESSION_REFRESH_EACH_REQUEST': True,
    'SESSION_COOKIE_PATH': '/'
}

# File-based session directory (if using filesystem for sessions)
SESSION_FILE_DIR = SESSIONS_DIR

# ==============================================
# TIMEZONE SETTINGS
# ==============================================
import pytz
TIMEZONE = 'Africa/Addis_Adaba'
TZ = pytz.timezone(TIMEZONE)

# ==============================================
# SECURITY FUNCTIONS (Python equivalents)
# ==============================================

def sanitize(data):
    """
    Sanitize output to prevent XSS.
    Equivalent to PHP's htmlspecialchars()
    """
    if data is None:
        return ''
    if isinstance(data, (list, dict)):
        return data
    import html
    return html.escape(str(data), quote=True)

def sanitize_data(data):
    """
    Recursively sanitize data (strings, lists, dicts)
    """
    if isinstance(data, dict):
        return {key: sanitize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, str):
        return sanitize(data)
    else:
        return data

def redirect(url):
    """
    Helper function for redirects.
    In Flask, use: return redirect(url)
    This function is provided for compatibility.
    """
    from flask import redirect as flask_redirect
    return flask_redirect(url)

# ==============================================
# DATABASE CONNECTION FUNCTION (PDO style)
# ==============================================

def get_db_connection():
    """
    Get a database connection using mysql.connector.
    Equivalent to PDO connection in PHP.
    """
    import mysql.connector
    from mysql.connector import Error
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        logger.error(f"Database connection failed: {e}")
        raise Exception("Database connection error. Please try again later.") from e

# ==============================================
# DATABASE CONNECTION CONTEXT MANAGER (for PDO-style transactions)
# ==============================================

class Database:
    """
    Context manager for database connections.
    Example usage:
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            results = cursor.fetchall()
    """
    def __enter__(self):
        self.conn = get_db_connection()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is not None:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()

# ==============================================
# FLASK APP CONFIGURATION
# ==============================================

def configure_app(app):
    """
    Configure Flask app with all settings.
    Call this in your main app.py file.
    """
    # Session settings
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['SESSION_COOKIE_NAME'] = SESSION_CONFIG['SESSION_COOKIE_NAME']
    app.config['SESSION_COOKIE_HTTPONLY'] = SESSION_CONFIG['SESSION_COOKIE_HTTPONLY']
    app.config['SESSION_COOKIE_SECURE'] = SESSION_CONFIG['SESSION_COOKIE_SECURE']
    app.config['SESSION_COOKIE_SAMESITE'] = SESSION_CONFIG['SESSION_COOKIE_SAMESITE']
    app.config['PERMANENT_SESSION_LIFETIME'] = SESSION_CONFIG['PERMANENT_SESSION_LIFETIME']
    app.config['SESSION_REFRESH_EACH_REQUEST'] = SESSION_CONFIG['SESSION_REFRESH_EACH_REQUEST']
    
    # Debug mode
    app.config['DEBUG'] = DEBUG_MODE
    
    # Database config (for Flask extensions if needed)
    app.config['MYSQL_HOST'] = DB_CONFIG['host']
    app.config['MYSQL_USER'] = DB_CONFIG['user']
    app.config['MYSQL_PASSWORD'] = DB_CONFIG['password']
    app.config['MYSQL_DB'] = DB_CONFIG['database']
    
    # Session file directory (if using Flask-Session)
    app.config['SESSION_FILE_DIR'] = str(SESSION_FILE_DIR)
    app.config['SESSION_TYPE'] = 'filesystem'  # or 'redis', 'memcached'
    
    # Logging
    if not DEBUG_MODE:
        # In production, log to file only
        for handler in app.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                app.logger.removeHandler(handler)

# ==============================================
# DEBUGGING HELPERS (Development only)
# ==============================================

def debug_print(data):
    """
    Pretty print data for debugging (development only)
    Equivalent to PHP's debug() function
    """
    if ENVIRONMENT == 'development':
        import pprint
        print("[DEBUG]")
        pprint.pprint(data)
        print("-" * 50)

def get_environment():
    """Get current environment"""
    return ENVIRONMENT

def is_development():
    """Check if running in development mode"""
    return ENVIRONMENT == 'development'

def is_production():
    """Check if running in production mode"""
    return ENVIRONMENT == 'production'

# ==============================================
# IMPORTANT: For MySQL Connector error handling
# ==============================================

# Define common MySQL error codes (for reference)
MYSQL_ERRORS = {
    'DUPLICATE_ENTRY': 1062,
    'CONNECTION_REFUSED': 2003,
    'ACCESS_DENIED': 1045,
    'UNKNOWN_DATABASE': 1049,
    'TABLE_EXISTS': 1050,
}

# ==============================================
# INITIALIZATION (Run when config is loaded)
# ==============================================

if __name__ == "__main__":
    # Test configuration
    print(f"APP_NAME: {APP_NAME}")
    print(f"ENVIRONMENT: {ENVIRONMENT}")
    print(f"BASE_URL: {BASE_URL}")
    print(f"Database Host: {DB_CONFIG['host']}")
    print(f"Database Name: {DB_CONFIG['database']}")
    print(f"Session directory: {SESSION_FILE_DIR}")
    print(f"Logs directory: {LOGS_DIR}")
    
    # Test database connection
    try:
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            print("Database connection: SUCCESS")
    except Exception as e:
        print(f"Database connection: FAILED - {e}")