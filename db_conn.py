# ==============================================
# db_conn.py - Database Connection (PDO style)
# Python equivalent of PHP's PDO connection
# ==============================================

import mysql.connector
from mysql.connector import Error
import logging

# Database configuration (same as PHP)
DB_HOST = 'localhost'
DB_NAME = 'roster'      # Your actual database name
DB_USER = 'root'        # Default XAMPP username
DB_PASS = ''            # Default XAMPP password (empty)
DB_CHARSET = 'utf8mb4'

# Connection options (similar to PDO options)
CONNECTION_OPTIONS = {
    'host': DB_HOST,
    'database': DB_NAME,
    'user': DB_USER,
    'password': DB_PASS,
    'charset': DB_CHARSET,
    'use_pure': True,                    # Use pure Python implementation
    'autocommit': False,                 # Like PDO with transactions
    'raise_on_warnings': True,           # Like PDO::ERRMODE_EXCEPTION
    'connection_timeout': 30,
    'pool_name': 'roster_pool',
    'pool_size': 5
}

# ==============================================
# PDO-Style Connection Class
# ==============================================

class PDOStyleConnection:
    """
    A PDO-style database connection wrapper.
    Mimics PHP PDO behavior in Python.
    """
    
    def __init__(self):
        self.connection = None
        self.error = None
        self._connect()
    
    def _connect(self):
        """Establish database connection (like PDO constructor)"""
        try:
            self.connection = mysql.connector.connect(**CONNECTION_OPTIONS)
            self.error = None
        except Error as e:
            self.error = str(e)
            raise Exception(f"Database connection failed: {e}")
    
    def prepare(self, sql):
        """
        Prepare a SQL statement (like PDO::prepare)
        Returns a Statement object
        """
        if not self.connection:
            self._connect()
        
        cursor = self.connection.cursor(dictionary=True)
        return Statement(cursor, sql)
    
    def query(self, sql):
        """
        Execute a query (like PDO::query)
        Returns result set for SELECT, or row count for INSERT/UPDATE/DELETE
        """
        if not self.connection:
            self._connect()
        
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql)
            
            # Check if this is a SELECT query
            if sql.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                # For INSERT/UPDATE/DELETE, return number of affected rows
                row_count = cursor.rowcount
                self.connection.commit()
                cursor.close()
                return row_count
        except Error as e:
            cursor.close()
            raise Exception(f"Query failed: {e}")
    
    def execute(self, sql, params=None):
        """
        Execute a prepared statement (like PDOStatement::execute)
        """
        if not self.connection:
            self._connect()
        
        cursor = self.connection.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # Check if this is a SELECT query
            if sql.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                row_count = cursor.rowcount
                self.connection.commit()
                cursor.close()
                return row_count
        except Error as e:
            cursor.close()
            raise Exception(f"Execute failed: {e}")
    
    def lastInsertId(self):
        """Get last insert ID (like PDO::lastInsertId)"""
        if self.connection:
            return self.connection.last_insert_rowid()
        return None
    
    def beginTransaction(self):
        """Begin a transaction (like PDO::beginTransaction)"""
        if self.connection:
            self.connection.start_transaction()
    
    def commit(self):
        """Commit transaction (like PDO::commit)"""
        if self.connection:
            self.connection.commit()
    
    def rollBack(self):
        """Rollback transaction (like PDO::rollBack)"""
        if self.connection:
            self.connection.rollback()
    
    def quote(self, string):
        """Quote a string for use in SQL (like PDO::quote)"""
        if self.connection:
            return self.connection.converter.escape(string)
        return string.replace("'", "''")
    
    def close(self):
        """Close the connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def errorCode(self):
        """Get error code (like PDO::errorCode)"""
        if self.error:
            return self.error
        return None
    
    def errorInfo(self):
        """Get error info (like PDO::errorInfo)"""
        if self.error:
            return [self.error]
        return []


class Statement:
    """
    PDO-style prepared statement wrapper
    """
    def __init__(self, cursor, sql):
        self.cursor = cursor
        self.sql = sql
        self.result = None
    
    def execute(self, params=None):
        """
        Execute prepared statement (like PDOStatement::execute)
        """
        try:
            if params:
                # Convert params to tuple if needed
                if isinstance(params, dict):
                    self.cursor.execute(self.sql, params)
                else:
                    self.cursor.execute(self.sql, params)
            else:
                self.cursor.execute(self.sql)
            
            self.result = self.cursor.fetchall()
            return True
        except Error as e:
            raise Exception(f"Statement execution failed: {e}")
    
    def fetch(self):
        """
        Fetch next row (like PDOStatement::fetch)
        """
        if self.result and len(self.result) > 0:
            return self.result.pop(0)
        return None
    
    def fetchAll(self):
        """
        Fetch all rows (like PDOStatement::fetchAll)
        """
        return self.result
    
    def rowCount(self):
        """
        Get number of affected rows (like PDOStatement::rowCount)
        """
        return self.cursor.rowcount
    
    def close(self):
        """Close the statement cursor"""
        if self.cursor:
            self.cursor.close()


# ==============================================
# Simple connection function (most commonly used)
# ==============================================

def get_pdo():
    """
    Get a PDO-style database connection.
    Equivalent to PHP's: return $pdo;
    
    Usage:
        pdo = get_pdo()
        result = pdo.query("SELECT * FROM users")
        for row in result:
            print(row)
    """
    return PDOStyleConnection()


# ==============================================
# Context manager for automatic connection handling
# ==============================================

class DatabaseConnection:
    """
    Context manager for database connections.
    Automatically handles connection and cleanup.
    
    Usage:
        with DatabaseConnection() as pdo:
            result = pdo.query("SELECT * FROM users")
            print(result)
    """
    def __enter__(self):
        self.pdo = get_pdo()
        return self.pdo
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pdo.close()


# ==============================================
# Simple connection function (direct connection)
# ==============================================

def get_db_connection():
    """
    Get a direct mysql.connector connection.
    More lightweight than PDO-style wrapper.
    
    Usage:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
    """
    try:
        conn = mysql.connector.connect(**CONNECTION_OPTIONS)
        return conn
    except Error as e:
        raise Exception(f"Database connection failed: {e}")


# ==============================================
# Test connection (like PHP's try-catch)
# ==============================================

if __name__ == "__main__":
    print("Testing database connection...")
    
    # Method 1: Using PDO-style wrapper
    try:
        print("\n1. Testing PDO-style connection:")
        pdo = get_pdo()
        result = pdo.query("SELECT DATABASE() as db_name")
        print(f"   ✅ Connected to database: {result[0]['db_name']}")
        pdo.close()
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Method 2: Using direct connection
    try:
        print("\n2. Testing direct connection:")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()
        print(f"   ✅ Total users: {count['count']}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Method 3: Using context manager
    try:
        print("\n3. Testing context manager:")
        with DatabaseConnection() as pdo:
            result = pdo.query("SELECT COUNT(*) as count FROM users")
            print(f"   ✅ Total users: {result[0]['count']}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")