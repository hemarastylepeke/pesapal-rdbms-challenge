"""
Database initialization script for SimpleRDBMS
Run this before using Django commands
"""

from simple_rdbms import SimpleRDBMS, Column, DataType

def init_database(db_path='simpledb.json'):
    """Initialize the database with required tables"""
    db = SimpleRDBMS(db_path)
    
    # Create django_migrations table (required by Django)
    try:
        sql = "CREATE TABLE django_migrations (id INTEGER PRIMARY KEY, app TEXT, name TEXT, applied TEXT)"
        db.execute(sql)
        print("✓ Created django_migrations table")
    except ValueError as e:
        if "already exists" in str(e):
            print("✓ django_migrations table already exists")
        else:
            raise
    
    # Create django_content_type table (required by contenttypes app)
    try:
        sql = "CREATE TABLE django_content_type (id INTEGER PRIMARY KEY, app_label TEXT, model TEXT)"
        db.execute(sql)
        print("✓ Created django_content_type table")
    except ValueError as e:
        if "already exists" in str(e):
            print("✓ django_content_type table already exists")
        else:
            raise
    
    # Create tasks table
    try:
        sql = "CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT, description TEXT, completed BOOLEAN, priority INTEGER)"
        db.execute(sql)
        print("✓ Created tasks table")
    except ValueError as e:
        if "already exists" in str(e):
            print("✓ tasks table already exists")
        else:
            raise
    
    # Create categories table
    try:
        sql = "CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT UNIQUE, description TEXT)"
        db.execute(sql)
        print("✓ Created categories table")
    except ValueError as e:
        if "already exists" in str(e):
            print("✓ categories table already exists")
        else:
            raise
    
    # Create task_categories junction table
    try:
        sql = "CREATE TABLE task_categories (id INTEGER PRIMARY KEY, task_id INTEGER, category_id INTEGER)"
        db.execute(sql)
        print("✓ Created task_categories table")
    except ValueError as e:
        if "already exists" in str(e):
            print("✓ task_categories table already exists")
        else:
            raise
    
    # Add some sample data
    print("\n📝 Adding sample data...")
    
    try:
        db.execute("INSERT INTO tasks (id, title, description, completed, priority) VALUES (1, 'Welcome to SimpleRDBMS', 'This is your first task. Try editing or deleting it!', False, 2)")
        print("✓ Added sample task 1")
    except:
        print("  Sample task 1 already exists")
    
    try:
        db.execute("INSERT INTO tasks (id, title, description, completed, priority) VALUES (2, 'Test the REPL', 'Run python simple_rdbms.py to try the interactive mode', False, 1)")
        print("✓ Added sample task 2")
    except:
        print("  Sample task 2 already exists")
    
    try:
        db.execute("INSERT INTO tasks (id, title, description, completed, priority) VALUES (3, 'Create a category', 'Navigate to the categories page and add your first category', False, 3)")
        print("✓ Added sample task 3")
    except:
        print("  Sample task 3 already exists")
    
    try:
        db.execute("INSERT INTO categories (id, name, description) VALUES (1, 'Work', 'Work-related tasks')")
        print("✓ Added sample category 1")
    except:
        print("  Sample category 1 already exists")
    
    try:
        db.execute("INSERT INTO categories (id, name, description) VALUES (2, 'Personal', 'Personal tasks and errands')")
        print("✓ Added sample category 2")
    except:
        print("  Sample category 2 already exists")
    
    print("\n✅ Database initialization complete!")
    print(f"📁 Database file: {db_path}")
    print("\n🚀 Next steps:")
    print("   python manage.py runserver")
    print("\n🌐 Then visit:")
    print("   http://127.0.0.1:8000/")

if __name__ == "__main__":
    init_database()