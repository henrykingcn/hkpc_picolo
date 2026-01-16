"""
Database Migration: Add employee_id to access_logs table
Run this script to update existing database
"""
import sqlite3
import os

def migrate_database():
    """Add employee_id column to access_logs table"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run the app first to create the database.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if employee_id column already exists
        cursor.execute("PRAGMA table_info(access_logs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'employee_id' in columns:
            print("✓ Column 'employee_id' already exists in access_logs table")
            conn.close()
            return True
        
        # Add employee_id column
        print("Adding 'employee_id' column to access_logs table...")
        cursor.execute("""
            ALTER TABLE access_logs 
            ADD COLUMN employee_id VARCHAR(50)
        """)
        
        # Update existing records with employee_id from authorized_persons
        print("Updating existing records with employee_id...")
        cursor.execute("""
            UPDATE access_logs 
            SET employee_id = (
                SELECT employee_id 
                FROM authorized_persons 
                WHERE authorized_persons.id = access_logs.person_id
            )
            WHERE person_id IS NOT NULL
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Migration completed successfully!")
        print("   - Added 'employee_id' column to access_logs")
        print("   - Updated existing records")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration: Add employee_id to access_logs")
    print("=" * 60)
    print()
    
    success = migrate_database()
    
    print()
    if success:
        print("✅ You can now run the application!")
    else:
        print("❌ Migration failed. Please check the error messages above.")
    print()

