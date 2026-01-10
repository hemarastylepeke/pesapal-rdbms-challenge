import re
import pickle
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum


class DataType(Enum):
    INTEGER = "INTEGER"
    TEXT = "TEXT"
    REAL = "REAL"


class Column:
    def __init__(self, name: str, dtype: DataType, primary_key: bool = False, 
                 unique: bool = False, not_null: bool = False):
        self.name = name
        self.dtype = dtype
        self.primary_key = primary_key
        self.unique = unique
        self.not_null = not_null


class Index:
    def __init__(self, column_name: str):
        self.column_name = column_name
        self.index: Dict[Any, Set[int]] = {}  # value -> set of row_ids
    
    def add(self, value: Any, row_id: int):
        if value not in self.index:
            self.index[value] = set()
        self.index[value].add(row_id)
    
    def remove(self, value: Any, row_id: int):
        if value in self.index:
            self.index[value].discard(row_id)
            if not self.index[value]:
                del self.index[value]
    
    def lookup(self, value: Any) -> Set[int]:
        return self.index.get(value, set())


class Table:
    def __init__(self, name: str, columns: List[Column]):
        self.name = name
        self.columns = {col.name: col for col in columns}
        self.rows: Dict[int, Dict[str, Any]] = {}
        self.next_id = 1
        self.indexes: Dict[str, Index] = {}
        
        # Auto-index primary key and unique columns
        for col in columns:
            if col.primary_key or col.unique:
                self.indexes[col.name] = Index(col.name)
    
    def _validate_row(self, row: Dict[str, Any], row_id: Optional[int] = None, is_insert: bool = False):
        for col_name, col in self.columns.items():
            value = row.get(col_name)
            
            if value is None:
                # Allow NULL for primary key during INSERT (will be auto-generated)
                if col.primary_key and is_insert:
                    continue
                if col.not_null or col.primary_key:
                    raise ValueError(f"Column {col_name} cannot be NULL")
                continue
            
            # Type checking
            if col.dtype == DataType.INTEGER and not isinstance(value, int):
                raise TypeError(f"Column {col_name} must be INTEGER")
            elif col.dtype == DataType.TEXT and not isinstance(value, str):
                raise TypeError(f"Column {col_name} must be TEXT")
            elif col.dtype == DataType.REAL and not isinstance(value, (int, float)):
                raise TypeError(f"Column {col_name} must be REAL")
            
            # Uniqueness check
            if (col.primary_key or col.unique) and col_name in self.indexes:
                existing = self.indexes[col_name].lookup(value)
                if row_id:
                    existing.discard(row_id)
                if existing:
                    raise ValueError(f"Duplicate value for {col_name}: {value}")
    
    def insert(self, row: Dict[str, Any]) -> int:
        # Find primary key column
        pk_col = None
        for col_name, col in self.columns.items():
            if col.primary_key:
                pk_col = col_name
                break
        
        # Auto-generate primary key if not provided
        if pk_col and (pk_col not in row or row[pk_col] is None):
            row[pk_col] = self.next_id
        
        # If primary key was provided, use it
        if pk_col and pk_col in row:
            row_id = row[pk_col]
            # Update next_id if needed
            if row_id >= self.next_id:
                self.next_id = row_id + 1
        else:
            row_id = self.next_id
            self.next_id += 1
        
        self._validate_row(row, is_insert=True)
        self.rows[row_id] = row.copy()
        
        # Update indexes
        for col_name, idx in self.indexes.items():
            if col_name in row and row[col_name] is not None:
                idx.add(row[col_name], row_id)
        
        return row_id
    
    def update(self, row_id: int, updates: Dict[str, Any]):
        if row_id not in self.rows:
            raise ValueError(f"Row {row_id} not found")
        
        old_row = self.rows[row_id].copy()
        new_row = old_row.copy()
        new_row.update(updates)
        
        self._validate_row(new_row, row_id)
        
        # Update indexes
        for col_name, idx in self.indexes.items():
            if col_name in updates:
                old_val = old_row.get(col_name)
                new_val = updates[col_name]
                if old_val is not None:
                    idx.remove(old_val, row_id)
                if new_val is not None:
                    idx.add(new_val, row_id)
        
        self.rows[row_id] = new_row
    
    def delete(self, row_id: int):
        if row_id not in self.rows:
            raise ValueError(f"Row {row_id} not found")
        
        row = self.rows[row_id]
        for col_name, idx in self.indexes.items():
            if col_name in row and row[col_name] is not None:
                idx.remove(row[col_name], row_id)
        
        del self.rows[row_id]
    
    def select(self, where: Optional[callable] = None) -> List[Tuple[int, Dict[str, Any]]]:
        results = []
        for row_id, row in self.rows.items():
            if where is None or where(row):
                results.append((row_id, row.copy()))
        return results
    
    def create_index(self, column_name: str):
        if column_name not in self.columns:
            raise ValueError(f"Column {column_name} does not exist")
        
        if column_name in self.indexes:
            return
        
        idx = Index(column_name)
        for row_id, row in self.rows.items():
            if column_name in row and row[column_name] is not None:
                idx.add(row[column_name], row_id)
        
        self.indexes[column_name] = idx


class Database:
    def __init__(self):
        self.tables: Dict[str, Table] = {}
    
    def create_table(self, name: str, columns: List[Column]):
        if name in self.tables:
            raise ValueError(f"Table {name} already exists")
        self.tables[name] = Table(name, columns)
    
    def drop_table(self, name: str):
        if name not in self.tables:
            raise ValueError(f"Table {name} does not exist")
        del self.tables[name]
    
    def get_table(self, name: str) -> Table:
        if name not in self.tables:
            raise ValueError(f"Table {name} does not exist")
        return self.tables[name]
    
    def save(self, filename: str):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod
    def load(filename: str) -> 'Database':
        with open(filename, 'rb') as f:
            return pickle.load(f)


class SQLParser:
    @staticmethod
    def parse(sql: str) -> Tuple[str, Dict[str, Any]]:
        # Remove leading/trailing whitespace and semicolon
        sql = sql.strip().rstrip(';')
        # Normalize whitespace (collapse multiple spaces/newlines into single space)
        sql = re.sub(r'\s+', ' ', sql)
        
        # CREATE TABLE
        match = re.match(r'CREATE TABLE (\w+)\s*\((.*)\)', sql, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            col_defs = match.group(2)
            columns = []
            
            for col_def in col_defs.split(','):
                col_def = col_def.strip()
                parts = col_def.split()
                col_name = parts[0]
                col_type = DataType[parts[1].upper()]
                
                pk = 'PRIMARY' in col_def.upper() and 'KEY' in col_def.upper()
                unique = 'UNIQUE' in col_def.upper()
                not_null = 'NOT' in col_def.upper() and 'NULL' in col_def.upper()
                
                columns.append(Column(col_name, col_type, pk, unique, not_null))
            
            return ('CREATE_TABLE', {'name': table_name, 'columns': columns})
        
        # INSERT
        match = re.match(r'INSERT INTO (\w+)\s*\((.*?)\)\s*VALUES\s*\((.*?)\)', sql, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            columns = [c.strip() for c in match.group(2).split(',')]
            values = [v.strip().strip("'\"") for v in match.group(3).split(',')]
            
            # Type conversion
            row = {}
            for col, val in zip(columns, values):
                if val.upper() == 'NULL':
                    row[col] = None
                elif val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
                    row[col] = int(val)
                elif val.replace('.', '', 1).isdigit():
                    row[col] = float(val)
                else:
                    row[col] = val
            
            return ('INSERT', {'table': table_name, 'row': row})
        
        # SELECT
        match = re.match(r'SELECT \* FROM (\w+)(?:\s+WHERE\s+(.+?))?(?:\s+JOIN\s+(\w+)\s+ON\s+(.+))?$', sql, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            where_clause = match.group(2)
            join_table = match.group(3)
            join_on = match.group(4)
            
            where_func = None
            if where_clause:
                where_func = SQLParser._parse_where(where_clause)
            
            return ('SELECT', {
                'table': table_name,
                'where': where_func,
                'join_table': join_table,
                'join_on': join_on
            })
        
        # UPDATE
        match = re.match(r'UPDATE (\w+) SET (.+?) WHERE (.+)', sql, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            set_clause = match.group(2)
            where_clause = match.group(3)
            
            updates = {}
            for assign in set_clause.split(','):
                col, val = assign.split('=')
                col = col.strip()
                val = val.strip().strip("'\"")
                
                if val.upper() == 'NULL':
                    updates[col] = None
                elif val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
                    updates[col] = int(val)
                elif val.replace('.', '', 1).isdigit():
                    updates[col] = float(val)
                else:
                    updates[col] = val
            
            where_func = SQLParser._parse_where(where_clause)
            
            return ('UPDATE', {'table': table_name, 'updates': updates, 'where': where_func})
        
        # DELETE
        match = re.match(r'DELETE FROM (\w+) WHERE (.+)', sql, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            where_clause = match.group(2)
            where_func = SQLParser._parse_where(where_clause)
            
            return ('DELETE', {'table': table_name, 'where': where_func})
        
        # CREATE INDEX
        match = re.match(r'CREATE INDEX ON (\w+)\s*\((\w+)\)', sql, re.IGNORECASE)
        if match:
            return ('CREATE_INDEX', {'table': match.group(1), 'column': match.group(2)})
        
        # DROP TABLE
        match = re.match(r'DROP TABLE (\w+)', sql, re.IGNORECASE)
        if match:
            return ('DROP_TABLE', {'table': match.group(1)})
        
        raise ValueError(f"Cannot parse SQL: {sql}")
    
    @staticmethod
    def _parse_where(where_clause: str) -> callable:
        match = re.match(r'(\w+)\s*=\s*(.+)', where_clause.strip())
        if match:
            col = match.group(1)
            val = match.group(2).strip().strip("'\"")
            
            if val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
                val = int(val)
            elif val.replace('.', '', 1).isdigit():
                val = float(val)
            
            return lambda row: row.get(col) == val
        
        raise ValueError(f"Cannot parse WHERE clause: {where_clause}")


class RDBMS:
    def __init__(self):
        self.db = Database()
    
    def execute(self, sql: str) -> Any:
        cmd, params = SQLParser.parse(sql)
        
        if cmd == 'CREATE_TABLE':
            self.db.create_table(params['name'], params['columns'])
            return f"Table {params['name']} created"
        
        elif cmd == 'DROP_TABLE':
            self.db.drop_table(params['table'])
            return f"Table {params['table']} dropped"
        
        elif cmd == 'INSERT':
            table = self.db.get_table(params['table'])
            row_id = table.insert(params['row'])
            return f"Inserted row with id {row_id}"
        
        elif cmd == 'SELECT':
            table = self.db.get_table(params['table'])
            results = table.select(params['where'])
            
            if params['join_table']:
                return self._execute_join(table, params['join_table'], params['join_on'], results)
            
            return results
        
        elif cmd == 'UPDATE':
            table = self.db.get_table(params['table'])
            rows = table.select(params['where'])
            for row_id, _ in rows:
                table.update(row_id, params['updates'])
            return f"Updated {len(rows)} rows"
        
        elif cmd == 'DELETE':
            table = self.db.get_table(params['table'])
            rows = table.select(params['where'])
            for row_id, _ in rows:
                table.delete(row_id)
            return f"Deleted {len(rows)} rows"
        
        elif cmd == 'CREATE_INDEX':
            table = self.db.get_table(params['table'])
            table.create_index(params['column'])
            return f"Index created on {params['table']}.{params['column']}"
        
        raise ValueError(f"Unknown command: {cmd}")
    
    def _execute_join(self, left_table: Table, right_table_name: str, 
                     join_on: str, left_results: List[Tuple[int, Dict]]) -> List[Dict]:
        right_table = self.db.get_table(right_table_name)
        
        # Parse join condition (e.g., "table1.col = table2.col")
        match = re.match(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', join_on)
        if not match:
            raise ValueError(f"Cannot parse JOIN ON: {join_on}")
        
        left_col = match.group(2) if match.group(1) == left_table.name else match.group(4)
        right_col = match.group(4) if match.group(1) == left_table.name else match.group(2)
        
        results = []
        for left_id, left_row in left_results:
            left_val = left_row.get(left_col)
            if left_val is None:
                continue
            
            for right_id, right_row in right_table.rows.items():
                if right_row.get(right_col) == left_val:
                    joined = {f"{left_table.name}.{k}": v for k, v in left_row.items()}
                    joined.update({f"{right_table_name}.{k}": v for k, v in right_row.items()})
                    results.append(joined)
        
        return results
    
    def repl(self):
        print("Simple RDBMS - Type 'exit' to quit")
        print("=" * 50)
        
        while True:
            try:
                sql = input("sql> ").strip()
                
                if sql.lower() == 'exit':
                    break
                
                if not sql:
                    continue
                
                result = self.execute(sql)
                
                if isinstance(result, list):
                    for item in result:
                        print(item)
                    print(f"\n{len(result)} rows")
                else:
                    print(result)
                
                print()
            
            except Exception as e:
                print(f"Error: {e}\n")


if __name__ == "__main__":
    rdbms = RDBMS()
    rdbms.repl()