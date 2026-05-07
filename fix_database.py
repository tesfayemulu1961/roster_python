import mysql.connector
from mysql.connector import Error

# Database connection
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'roster'
}

def get_connection():
    return mysql.connector.connect(**db_config)

def update_parent_ids():
    """Update parent p_id to PAR-1, PAR-2, etc. format, starting from PAR-160 for new records"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # First, get the next available PAR number starting from 160
    cursor.execute("SELECT MAX(CAST(SUBSTRING(p_id, 5) AS UNSIGNED)) FROM parent WHERE p_id REGEXP '^PAR-[0-9]+$'")
    result = cursor.fetchone()
    max_par = result[0] if result[0] else 0
    next_par = max(max_par + 1, 160)  # Start from PAR-160
    
    # Update existing parents with proper PAR-XXX format
    cursor.execute("SELECT ID, p_id FROM parent WHERE p_id IS NULL OR p_id = '' OR p_id NOT REGEXP '^PAR-[0-9]+$'")
    parents = cursor.fetchall()
    
    for parent_id, old_p_id in parents:
        new_p_id = f'PAR-{next_par}'
        cursor.execute("UPDATE parent SET p_id = %s WHERE ID = %s", (new_p_id, parent_id))
        print(f"Updated parent ID {parent_id}: {old_p_id} -> {new_p_id}")
        next_par += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Updated {len(parents)} parents. Next PAR ID will be PAR-{next_par}")

def remove_parent_id_from_student():
    """Remove parent_id from student table to break circular reference"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if parent_id column exists
    cursor.execute("SHOW COLUMNS FROM student LIKE 'parent_id'")
    if cursor.fetchone():
        # First, save the relationships to a junction table if needed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_parent_relationship (
                student_RN INT,
                parent_id INT,
                PRIMARY KEY (student_RN, parent_id)
            )
        """)
        
        # Save existing relationships
        cursor.execute("INSERT INTO student_parent_relationship (student_RN, parent_id) SELECT RN, parent_id FROM student WHERE parent_id IS NOT NULL")
        print(f"✅ Saved {cursor.rowcount} student-parent relationships to student_parent_relationship table")
        
        # Remove parent_id column from student
        cursor.execute("ALTER TABLE student DROP COLUMN parent_id")
        print("✅ Removed parent_id column from student table")
    else:
        print("ℹ️ parent_id column doesn't exist in student table")
    
    conn.commit()
    cursor.close()
    conn.close()

def create_relationship_table():
    """Create a proper junction table for student-parent many-to-many relationship"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_parent (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_RN INT NOT NULL,
            parent_id INT NOT NULL,
            relationship_type VARCHAR(50) DEFAULT 'parent',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_RN) REFERENCES student(RN) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES parent(ID) ON DELETE CASCADE,
            UNIQUE KEY unique_student_parent (student_RN, parent_id)
        )
    """)
    print("✅ Created student_parent junction table")
    
    conn.commit()
    cursor.close()
    conn.close()

def auto_generate_par_id():
    """Create a function to auto-generate PAR IDs for new parents"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create a trigger to auto-generate PAR ID
    cursor.execute("DROP TRIGGER IF EXISTS before_insert_parent")
    cursor.execute("""
        CREATE TRIGGER before_insert_parent
        BEFORE INSERT ON parent
        FOR EACH ROW
        BEGIN
            DECLARE next_id INT;
            IF NEW.p_id IS NULL OR NEW.p_id = '' THEN
                SELECT COALESCE(MAX(CAST(SUBSTRING(p_id, 5) AS UNSIGNED)), 159) + 1 INTO next_id 
                FROM parent WHERE p_id REGEXP '^PAR-[0-9]+$';
                SET NEW.p_id = CONCAT('PAR-', next_id);
            END IF;
        END
    """)
    print("✅ Created trigger to auto-generate PAR IDs for new parents (starting from PAR-160)")
    
    conn.commit()
    cursor.close()
    conn.close()

def update_existing_student_parent_relationships():
    """Update the relationship table with existing data"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # First, ensure we have the relationship table
    cursor.execute("""
        INSERT IGNORE INTO student_parent (student_RN, parent_id)
        SELECT student_RN, parent_id FROM student_parent_relationship
    """)
    print(f"✅ Added relationships to student_parent table")
    
    conn.commit()
    cursor.close()
    conn.close()

def main():
    print("=" * 60)
    print("Database Schema Update Tool")
    print("=" * 60)
    
    print("\n1. Updating parent IDs to PAR-XXX format...")
    update_parent_ids()
    
    print("\n2. Creating junction table for student-parent relationships...")
    create_relationship_table()
    
    print("\n3. Removing parent_id from student table (breaking circular reference)...")
    remove_parent_id_from_student()
    
    print("\n4. Creating auto-generate trigger for PAR IDs...")
    auto_generate_par_id()
    
    print("\n" + "=" * 60)
    print("✅ All operations completed successfully!")
    print("=" * 60)
    
    print("\n📋 Summary:")
    print("   - Parent IDs are now in PAR-XXX format")
    print("   - parent_id column removed from student table")
    print("   - New student_parent junction table created")
    print("   - New parents will auto-generate PAR IDs starting from PAR-160")
    print("\n🔧 To add a parent-student relationship, use:")
    print("   INSERT INTO student_parent (student_RN, parent_id) VALUES (student_RN, parent_id);")

if __name__ == "__main__":
    main()