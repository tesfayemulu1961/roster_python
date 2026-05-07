# utils/activity_logger.py
import mysql.connector
from datetime import datetime
from flask import request
import logging

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_db_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def record_activity(user_id, username, user_type, action, details=''):
    """
    Record user activity in the activity_log table
    
    Parameters:
    - user_id: The user's ID (can be None or 0 for failed logins)
    - username: The username
    - user_type: The user's type (director, teacher, student, etc.)
    - action: The action performed (LOGIN, LOGOUT, LOGIN_FAILED, etc.)
    - details: Additional details about the action
    
    Returns:
    - bool: True if successful, False otherwise
    """
    
    # Get client information from Flask request context
    ip_address = None
    user_agent = None
    
    try:
        # Try to get request context (may not be available in all contexts)
        if request:
            ip_address = request.remote_addr
            user_agent = request.user_agent.string if request.user_agent else ''
    except RuntimeError:
        # Outside request context
        pass
    
    # Log the attempt
    logging.info(f"Attempting to record activity: user_id={user_id}, username={username}, action={action}, details={details}")
    
    # Handle invalid user_id (0 or negative) - set to NULL for foreign key constraint
    insert_user_id = None if (not user_id or user_id <= 0) else user_id
    
    conn = get_db_connection()
    if not conn:
        logging.error("Failed to connect to database")
        return False
    
    cursor = None
    result = False
    
    try:
        cursor = conn.cursor()
        
        # First attempt: Try with provided user_id (or NULL)
        cursor.execute("""
            INSERT INTO activity_log 
            (user_id, username, user_type, action, details, ip_address, user_agent, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, (insert_user_id, username, user_type, action, details, ip_address, user_agent))
        
        conn.commit()
        result = True
        logging.info(f"Activity recorded successfully: user_id={user_id}, action={action}")
        
    except mysql.connector.Error as e:
        error_msg = str(e)
        logging.error(f"Failed to record activity: {error_msg}")
        
        # If it failed due to foreign key constraint, try again with NULL user_id
        if 'foreign key constraint' in error_msg.lower() or 'cannot add or update' in error_msg.lower():
            logging.info("Foreign key constraint failed, retrying with NULL user_id")
            
            try:
                # Retry with explicit NULL user_id
                cursor.execute("""
                    INSERT INTO activity_log 
                    (user_id, username, user_type, action, details, ip_address, user_agent, created_at) 
                    VALUES (NULL, %s, %s, %s, %s, %s, %s, NOW())
                """, (username, user_type, action, details, ip_address, user_agent))
                
                conn.commit()
                result = True
                logging.info(f"Activity recorded successfully with NULL user_id: action={action}")
                
            except mysql.connector.Error as e2:
                logging.error(f"Second attempt also failed: {e2}")
                result = False
        
    except Exception as e:
        logging.error(f"Unexpected error recording activity: {e}")
        result = False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return result


def record_login_failure(username, reason, user_id=None):
    """
    Specifically record a failed login attempt
    
    Parameters:
    - username: The username that attempted to login
    - reason: The reason for failure (wrong password, inactive account, etc.)
    - user_id: Optional user_id (if known, otherwise None)
    
    Returns:
    - bool: True if successful, False otherwise
    """
    user_id = user_id or 0
    return record_activity(user_id, username, '', 'LOGIN_FAILED', reason)


def record_login_success(user_id, username, user_type):
    """
    Record a successful login
    
    Parameters:
    - user_id: The user's ID
    - username: The username
    - user_type: The user's type
    
    Returns:
    - bool: True if successful, False otherwise
    """
    return record_activity(user_id, username, user_type, 'LOGIN', f'User {username} logged in successfully')


def record_logout(user_id, username, user_type):
    """
    Record a logout
    
    Parameters:
    - user_id: The user's ID
    - username: The username
    - user_type: The user's type
    
    Returns:
    - bool: True if successful, False otherwise
    """
    return record_activity(user_id, username, user_type, 'LOGOUT', f'User {username} logged out')


def record_data_export(user_id, username, user_type, export_type, details=''):
    """
    Record data export activity
    
    Parameters:
    - user_id: The user's ID
    - username: The username
    - user_type: The user's type
    - export_type: Type of export (CSV, PDF, Excel, etc.)
    - details: Additional details about the export
    
    Returns:
    - bool: True if successful, False otherwise
    """
    action = f'EXPORT_{export_type.upper()}'
    detail_text = f'User {username} exported {export_type} data. {details}'
    return record_activity(user_id, username, user_type, action, detail_text)


def record_data_import(user_id, username, user_type, import_type, details=''):
    """
    Record data import activity
    
    Parameters:
    - user_id: The user's ID
    - username: The username
    - user_type: The user's type
    - import_type: Type of import (Excel, CSV, etc.)
    - details: Additional details about the import
    
    Returns:
    - bool: True if successful, False otherwise
    """
    action = f'IMPORT_{import_type.upper()}'
    detail_text = f'User {username} imported {import_type} data. {details}'
    return record_activity(user_id, username, user_type, action, detail_text)


def record_permission_change(user_id, username, user_type, target_user, action_type, details=''):
    """
    Record permission changes
    
    Parameters:
    - user_id: The user's ID making the change
    - username: The username making the change
    - user_type: The user's type
    - target_user: The user whose permissions were changed
    - action_type: Type of change (GRANT, REVOKE, UPDATE)
    - details: Additional details about the change
    
    Returns:
    - bool: True if successful, False otherwise
    """
    action = f'PERMISSION_{action_type.upper()}'
    detail_text = f'User {username} {action_type} permissions for user {target_user}. {details}'
    return record_activity(user_id, username, user_type, action, detail_text)


def record_student_operation(user_id, username, user_type, operation, student_name, details=''):
    """
    Record student-related operations
    
    Parameters:
    - user_id: The user's ID
    - username: The username
    - user_type: The user's type
    - operation: ADD, EDIT, DELETE, VIEW, etc.
    - student_name: The student's name or ID
    - details: Additional details
    
    Returns:
    - bool: True if successful, False otherwise
    """
    action = f'STUDENT_{operation.upper()}'
    detail_text = f'User {username} {operation} student {student_name}. {details}'
    return record_activity(user_id, username, user_type, action, detail_text)


def record_teacher_operation(user_id, username, user_type, operation, teacher_name, details=''):
    """
    Record teacher-related operations
    
    Parameters:
    - user_id: The user's ID
    - username: The username
    - user_type: The user's type
    - operation: ADD, EDIT, DELETE, ASSIGN, etc.
    - teacher_name: The teacher's name or ID
    - details: Additional details
    
    Returns:
    - bool: True if successful, False otherwise
    """
    action = f'TEACHER_{operation.upper()}'
    detail_text = f'User {username} {operation} teacher {teacher_name}. {details}'
    return record_activity(user_id, username, user_type, action, detail_text)


def record_settings_change(user_id, username, user_type, setting_name, old_value, new_value):
    """
    Record system settings changes
    
    Parameters:
    - user_id: The user's ID
    - username: The username
    - user_type: The user's type
    - setting_name: Name of the setting changed
    - old_value: Previous value
    - new_value: New value
    
    Returns:
    - bool: True if successful, False otherwise
    """
    details = f'Updated {setting_name} from "{old_value}" to "{new_value}"'
    return record_activity(user_id, username, user_type, 'SETTINGS_CHANGE', details)


# Convenience decorator for logging function calls
def log_activity(action_name):
    """
    Decorator to automatically log function calls
    
    Usage:
    @log_activity('USER_LOGIN')
    def login_user(username, password):
        # function code
        pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Execute the function
            result = func(*args, **kwargs)
            
            # Try to log the activity (if we have request context and session)
            try:
                from flask import session
                if session and session.get('logged_in'):
                    user_id = session.get('user_id')
                    username = session.get('username')
                    user_type = session.get('user_type')
                    
                    # Log the activity
                    record_activity(user_id, username, user_type, action_name, f"Executed {func.__name__}")
            except:
                # No session or request context, skip logging
                pass
            
            return result
        return wrapper
    return decorator


# Test function (can be removed in production)
def test_logger():
    """Test the activity logger functionality"""
    print("Testing activity logger...")
    
    # Test login success
    record_login_success(1, 'test_user', 'director')
    print("✓ Login success logged")
    
    # Test login failure
    record_login_failure('wrong_user', 'Invalid password')
    print("✓ Login failure logged")
    
    # Test logout
    record_logout(1, 'test_user', 'director')
    print("✓ Logout logged")
    
    print("Activity logger test complete!")


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    test_logger()