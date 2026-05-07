# ==============================================
# DATABASE CONFIGURATION - Python version
# ==============================================

import mysql.connector
from mysql.connector import Error
import logging

# Database configuration parameters
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster',
    'charset': 'utf8mb4',
    'autocommit': False,
    'use_pure': True,
    'pool_size': 5,
    'pool_name': 'roster_pool'
}

# Simple connection function (equivalent to mysqli_connect)
def get_db_connection():
    """
    Create and return a database connection.
    Equivalent to: $conn = new mysqli($servername, $username, $password, $dbname)
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        logging.error(f"Database connection failed: {e}")
        raise Exception(f"Connection failed: {e}")

# Global connection variable (similar to PHP's $conn)
# In PHP: $conn = new mysqli(...)
# In Python, we create a function instead of a global variable
# because connections_ don't persist across requests like in PHP

# Context manager for automatic connection handling
class DatabaseConnection:
    """
    Context manager for database connections.
    Automatically handles connection and cleanup.
    
    Usage:
        with DatabaseConnection() as conn:
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

# Simple test connection function (equivalent to checking $conn->connect_error)
def test_connection():
    """
    Test if database connection is working.
    Equivalent to checking mysqli_connect_error()
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"Connection failed: {e}")
        return False

# ==============================================
# For backward compatibility with existing code
# ==============================================

# If you want to maintain a similar pattern to PHP where you have a global $conn
# Note: In Flask, this is NOT recommended because connections don't persist
# across requests like in PHP. Use get_db_connection() instead.

# But for compatibility, you can create a connection per request using Flask's before_request

def init_db_for_flask(app):
    """
    Initialize database connection for Flask app.
    Use with before_request and teardown_request.
    """
    @app.before_request
    def before_request():
        from flask import g
        g.db = get_db_connection()
    
    @app.teardown_request
    def teardown_request(exception=None):
        from flask import g
        db = getattr(g, 'db', None)
        if db is not None:
            db.close()

# ==============================================
# If you prefer a global connection (like PHP)
# WARNING: This is not recommended for Flask
# ==============================================

# Global connection object (use with caution)
_global_conn = None

def get_global_connection():
    """
    Get or create a global database connection.
    Similar to PHP's persistent $conn.
    Use carefully - connections may time out.
    """
    global _global_conn
    if _global_conn is None or not _global_conn.is_connected():
        _global_conn = get_db_connection()
    return _global_conn

# MySQLi-style wrapper class (for those who prefer OOP style)
class MySQLiWrapper:
    """
    Wrapper class that mimics PHP's mysqli interface.
    """
    def __init__(self):
        self.connection = None
        self.error = None
    
    def connect(self):
        """Connect to database (like mysqli::__construct)"""
        try:
            self.connection = get_db_connection()
            return True
        except Exception as e:
            self.error = str(e)
            return False
    
    def query(self, sql, params=None):
        """Execute a query (like mysqli::query)"""
        if not self.connection:
            return None
        
        cursor = self.connection.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            if sql.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                self.connection.commit()
                return cursor.rowcount
        except Error as e:
            self.error = str(e)
            return None
        finally:
            cursor.close()
    
    def prepare(self, sql):
        """Prepare a statement (like mysqli::prepare)"""
        # This is a simplified version - use cursor.execute for prepared statements
        class Statement:
            def __init__(self, connection, sql):
                self.connection = connection
                self.sql = sql
                self.cursor = None
            
            def bind_param(self, types, *params):
                # Convert types string to actual parameters
                # This is simplified - use cursor.execute directly
                pass
            
            def execute(self):
                self.cursor = self.connection.cursor(dictionary=True)
                self.cursor.execute(self.sql)
                return True
            
            def get_result(self):
                return self.cursor.fetchall() if self.cursor else None
            
            def close(self):
                if self.cursor:
                    self.cursor.close()
        
        return Statement(self.connection, sql)
    
    def close(self):
        """Close connection (like mysqli::close)"""
        if self.connection:
            self.connection.close()
    
    def escape_string(self, string):
        """Escape string (like mysqli::real_escape_string)"""
        if self.connection:
            return self.connection.converter.escape(string)
        return string.replace("'", "''")

# ==============================================
# Usage examples
# ==============================================

if __name__ == "__main__":
    # Test the connection
    print("Testing database connection...")
    
    # Method 1: Direct connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()
        print(f"✅ Connected to database: {db_name[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    
    # Method 2: Using context manager
    print("\nUsing context manager:")
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users")
            count = cursor.fetchone()
            print(f"✅ Total users: {count[0]}")
            cursor.close()
    except Exception as e:
        print(f"❌ Query failed: {e}")
    
    # Method 3: Using MySQLi wrapper
    print("\nUsing MySQLi wrapper:")
    $mysqli = MySQLiWrapper()
    if $mysqli.connect():
        result = $mysqli.query("SELECT COUNT(*) as count FROM users")
        if result:
            print(f"✅ Total users: {result[0]['count']}")
        $mysqli.close()
    else:
        print(f"❌ Connection failed: {$mysqli.error}")