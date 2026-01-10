# ===== tasks/db_wrapper.py =====
"""
Wrapper around our custom RDBMS to make it easy to use in Django views.
This initializes the database with the required schema.
"""
import os
from pathlib import Path
from simple_rdbms import RDBMS, Column, DataType

# Store the database file in the project root
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / 'custom_rdbms.db'

class TaskDB:
    _instance = None
    _initialized = False
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RDBMS()
            
            # Try to load existing database
            if os.path.exists(DB_FILE):
                try:
                    from simple_rdbms import Database
                    cls._instance.db = Database.load(str(DB_FILE))
                    cls._initialized = True
                    print(f"Loaded existing database from {DB_FILE}")
                except Exception as e:
                    print(f"Failed to load database: {e}")
                    print("Initializing fresh database...")
                    cls._initialize_schema()
            else:
                print("No existing database found. Creating new one...")
                cls._initialize_schema()
        
        return cls._instance
    
    @classmethod
    def _initialize_schema(cls):
        """Initialize database schema with tables and sample data."""
        if cls._initialized:
            return
            
        rdbms = cls._instance
        
        try:
            # Create users table
            print("Creating users table...")
            rdbms.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE
                )
            """)
            
            # Create tasks table
            print("Creating tasks table...")
            rdbms.execute("""
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    priority INTEGER
                )
            """)
            
            # Create index on user_id for faster joins
            print("Creating index on tasks.user_id...")
            rdbms.execute("CREATE INDEX ON tasks (user_id)")
            
            # Add sample data
            print("Adding sample users...")
            rdbms.execute("""
                INSERT INTO users (name, email)
                VALUES ('Alice Smith', 'alice@example.com')
            """)
            
            rdbms.execute("""
                INSERT INTO users (name, email)
                VALUES ('Bob Jones', 'bob@example.com')
            """)
            
            # Save the initialized database
            cls.save()
            cls._initialized = True
            print("Database initialized successfully!")
            
        except ValueError as e:
            print(f"Warning during initialization: {e}")
            # Tables might already exist
            cls._initialized = True
        except Exception as e:
            print(f"Error during initialization: {e}")
            raise
    
    @classmethod
    def save(cls):
        """Save the database to disk."""
        if cls._instance:
            cls._instance.db.save(str(DB_FILE))
            print(f"Database saved to {DB_FILE}")