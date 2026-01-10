"""
Django database backend adapter for SimpleRDBMS
This allows Django to use our custom RDBMS as its database backend
"""

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.features import BaseDatabaseFeatures
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.base.client import BaseDatabaseClient
from django.db.backends.base.creation import BaseDatabaseCreation
from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db import NotSupportedError
import sys
import os

# Import our custom RDBMS
# Add parent directory to path to import simple_rdbms
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from simple_rdbms import SimpleRDBMS, DataType, Column


# Dummy Database module for Django's error handling
class Database:
    """Minimal Database module to satisfy Django's requirements"""
    class Error(Exception):
        pass
    class InterfaceError(Error):
        pass
    class DatabaseError(Error):
        pass
    class DataError(DatabaseError):
        pass
    class OperationalError(DatabaseError):
        pass
    class IntegrityError(DatabaseError):
        pass
    class InternalError(DatabaseError):
        pass
    class ProgrammingError(DatabaseError):
        pass
    class NotSupportedError(DatabaseError):
        pass


class DatabaseFeatures(BaseDatabaseFeatures):
    supports_transactions = False
    can_use_chunked_reads = False
    supports_foreign_keys = False
    supports_column_check_constraints = False
    supports_table_check_constraints = False
    can_introspect_foreign_keys = False
    has_bulk_insert = False
    supports_timezones = False
    supports_paramstyle_pyformat = False


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django.db.backends.sqlite3.compiler"
    
    def quote_name(self, name):
        return name
    
    def last_insert_id(self, cursor, table_name, pk_name):
        return cursor.lastrowid


class DatabaseClient(BaseDatabaseClient):
    executable_name = 'simpledb'


class DatabaseCreation(BaseDatabaseCreation):
    def create_test_db(self, *args, **kwargs):
        return None
    
    def destroy_test_db(self, *args, **kwargs):
        pass


class DatabaseIntrospection(BaseDatabaseIntrospection):
    def get_table_list(self, cursor):
        """Return a list of table names in the database"""
        # Access the RDBMS instance through the connection
        return [
            self.connection.TableInfo(name, 't') 
            for name in cursor.rdbms.db.tables.keys()
        ]
    
    def get_table_description(self, cursor, table_name):
        """Return description of table columns"""
        table = cursor.rdbms.db.get_table(table_name)
        descriptions = []
        for col_name, col in table.columns.items():
            descriptions.append((
                col_name,  # name
                col.data_type.value,  # type_code
                None,  # display_size
                None,  # internal_size
                None,  # precision
                None,  # scale
                col.nullable,  # null_ok
            ))
        return descriptions


class DatabaseSchemaEditor(BaseDatabaseSchemaEditor):
    def create_model(self, model):
        """Convert Django model to SimpleRDBMS table"""
        columns = []
        
        for field in model._meta.local_fields:
            col_name = field.column
            
            # Map Django field types to our DataType
            if field.get_internal_type() in ('AutoField', 'BigAutoField', 'IntegerField', 'SmallIntegerField', 'PositiveIntegerField'):
                col_type = DataType.INTEGER
            elif field.get_internal_type() in ('CharField', 'TextField', 'EmailField', 'URLField', 'SlugField'):
                col_type = DataType.TEXT
            elif field.get_internal_type() in ('FloatField', 'DecimalField'):
                col_type = DataType.REAL
            elif field.get_internal_type() == 'BooleanField':
                col_type = DataType.BOOLEAN
            else:
                col_type = DataType.TEXT
            
            columns.append(Column(
                name=col_name,
                data_type=col_type,
                primary_key=field.primary_key,
                unique=field.unique,
                nullable=field.null
            ))
        
        self.connection.rdbms.db.create_table(model._meta.db_table, columns)
        self.connection.rdbms.db.save()
    
    def delete_model(self, model):
        """Drop a table"""
        try:
            self.connection.rdbms.db.drop_table(model._meta.db_table)
            self.connection.rdbms.db.save()
        except ValueError:
            pass  # Table doesn't exist


class DatabaseCursor:
    """Cursor for executing queries"""
    def __init__(self, rdbms):
        self.rdbms = rdbms
        self.lastrowid = None
        self.rowcount = -1
        self._results = []
    
    def execute(self, sql, params=None):
        """Execute a SQL query"""
        # Very basic SQL execution with parameter substitution
        if params:
            # Simple parameter substitution
            for param in params:
                if isinstance(param, str):
                    sql = sql.replace('%s', f"'{param}'", 1)
                elif param is None:
                    sql = sql.replace('%s', 'NULL', 1)
                else:
                    sql = sql.replace('%s', str(param), 1)
        
        try:
            result = self.rdbms.execute(sql)
            if isinstance(result, list):
                self._results = result
                self.rowcount = len(result)
            elif isinstance(result, str) and 'Inserted row with ID' in result:
                # Extract the row ID from the result string
                import re
                match = re.search(r'ID (\d+)', result)
                if match:
                    self.lastrowid = int(match.group(1))
                self._results = []
                self.rowcount = 1
            else:
                self._results = []
                self.rowcount = 0
        except Exception as e:
            print(f"SQL Error: {e}")
            print(f"SQL: {sql}")
            self._results = []
            self.rowcount = -1
    
    def fetchall(self):
        """Fetch all results"""
        return [(row_id, *row.values()) for row_id, row in self._results]
    
    def fetchone(self):
        """Fetch one result"""
        if self._results:
            row_id, row = self._results[0]
            return (row_id, *row.values())
        return None
    
    def fetchmany(self, size=1):
        """Fetch multiple results"""
        results = []
        for i in range(min(size, len(self._results))):
            row_id, row = self._results[i]
            results.append((row_id, *row.values()))
        return results
    
    def close(self):
        """Close the cursor"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DatabaseWrapper(BaseDatabaseWrapper):
    vendor = 'simplerdbms'
    display_name = 'SimpleRDBMS'
    
    # Set the Database module
    Database = Database
    
    data_types = {
        'AutoField': 'INTEGER',
        'BigAutoField': 'INTEGER',
        'BooleanField': 'BOOLEAN',
        'CharField': 'TEXT',
        'DateField': 'TEXT',
        'DateTimeField': 'TEXT',
        'DecimalField': 'REAL',
        'FloatField': 'REAL',
        'IntegerField': 'INTEGER',
        'TextField': 'TEXT',
        'PositiveIntegerField': 'INTEGER',
        'SmallIntegerField': 'INTEGER',
    }
    
    operators = {
        'exact': '= %s',
        'iexact': "= %s",
        'contains': 'LIKE %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
    }
    
    SchemaEditorClass = DatabaseSchemaEditor
    client_class = DatabaseClient
    creation_class = DatabaseCreation
    features_class = DatabaseFeatures
    introspection_class = DatabaseIntrospection
    ops_class = DatabaseOperations
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rdbms = None
    
    def get_connection_params(self):
        """Return parameters for database connection"""
        settings = self.settings_dict
        return {
            'db_path': str(settings.get('NAME', 'simpledb.json'))
        }
    
    def get_new_connection(self, conn_params):
        """Create a new database connection"""
        self.rdbms = SimpleRDBMS(conn_params['db_path'])
        return self.rdbms
    
    def init_connection_state(self):
        """Initialize connection state"""
        pass
    
    def create_cursor(self, name=None):
        """Create a cursor for executing queries"""
        self.ensure_connection()
        return DatabaseCursor(self.rdbms)
    
    def _set_autocommit(self, autocommit):
        """Set autocommit mode (our DB always auto-commits)"""
        pass
    
    def is_usable(self):
        """Check if the connection is usable"""
        return self.rdbms is not None
    
    def _close(self):
        """Close the database connection"""
        if self.rdbms:
            self.rdbms.db.save()
        self.rdbms = None
    
    def ensure_connection(self):
        """Ensure we have a connection"""
        if self.connection is None:
            self.connect()