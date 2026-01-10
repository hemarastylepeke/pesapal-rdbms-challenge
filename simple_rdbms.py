"""
SimpleRDBMS - A minimal relational database management system
"""

import re
import json
import os
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class DataType(Enum):
    INTEGER = "INTEGER"
    TEXT = "TEXT"
    REAL = "REAL"
    BOOLEAN = "BOOLEAN"


@dataclass
class Column:
    name: str
    data_type: DataType
    primary_key: bool = False
    unique: bool = False
    nullable: bool = True


@dataclass
class Index:
    column: str
    index_map: Dict[Any, Set[int]] = field(default_factory=dict)
    
    def add(self, value: Any, row_id: int):
        if value not in self.index_map:
            self.index_map[value] = set()
        self.index_map[value].add(row_id)
    
    def remove(self, value: Any, row_id: int):
        if value in self.index_map:
            self.index_map[value].discard(row_id)
            if not self.index_map[value]:
                del self.index_map[value]
    
    def lookup(self, value: Any) -> Set[int]:
        return self.index_map.get(value, set())


class Table:
    def __init__(self, name: str, columns: List[Column]):
        self.name = name
        self.columns = {col.name: col for col in columns}
        self.rows: Dict[int, Dict[str, Any]] = {}
        self.next_id = 0
        self.indexes: Dict[str, Index] = {}
        
        # Create indexes for primary key and unique columns
        for col in columns:
            if col.primary_key or col.unique:
                self.indexes[col.name] = Index(col.name)
    
    def _validate_row(self, row: Dict[str, Any], row_id: Optional[int] = None) -> Dict[str, Any]:
        validated = {}
        
        for col_name, col in self.columns.items():
            value = row.get(col_name)
            
            # Check nullable
            if value is None:
                if not col.nullable and not col.primary_key:
                    raise ValueError(f"Column {col_name} cannot be NULL")
                validated[col_name] = None
                continue
            
            # Type conversion and validation
            if col.data_type == DataType.INTEGER:
                validated[col_name] = int(value)
            elif col.data_type == DataType.REAL:
                validated[col_name] = float(value)
            elif col.data_type == DataType.TEXT:
                validated[col_name] = str(value)
            elif col.data_type == DataType.BOOLEAN:
                validated[col_name] = bool(value)
            
            # Check unique constraint
            if col.unique or col.primary_key:
                if col_name in self.indexes:
                    existing = self.indexes[col_name].lookup(validated[col_name])
                    if row_id is not None:
                        existing.discard(row_id)
                    if existing:
                        raise ValueError(f"Duplicate value for unique column {col_name}")
        
        return validated
    
    def insert(self, row: Dict[str, Any]) -> int:
        validated = self._validate_row(row)
        row_id = self.next_id
        self.rows[row_id] = validated
        self.next_id += 1
        
        # Update indexes
        for col_name, index in self.indexes.items():
            if col_name in validated and validated[col_name] is not None:
                index.add(validated[col_name], row_id)
        
        return row_id
    
    def update(self, row_id: int, updates: Dict[str, Any]):
        if row_id not in self.rows:
            raise ValueError(f"Row {row_id} not found")
        
        old_row = self.rows[row_id].copy()
        new_row = {**old_row, **updates}
        validated = self._validate_row(new_row, row_id)
        
        # Update indexes
        for col_name, index in self.indexes.items():
            if col_name in old_row and old_row[col_name] is not None:
                index.remove(old_row[col_name], row_id)
            if col_name in validated and validated[col_name] is not None:
                index.add(validated[col_name], row_id)
        
        self.rows[row_id] = validated
    
    def delete(self, row_id: int):
        if row_id not in self.rows:
            raise ValueError(f"Row {row_id} not found")
        
        row = self.rows[row_id]
        
        # Update indexes
        for col_name, index in self.indexes.items():
            if col_name in row and row[col_name] is not None:
                index.remove(row[col_name], row_id)
        
        del self.rows[row_id]
    
    def select(self, where: Optional[callable] = None) -> List[Tuple[int, Dict[str, Any]]]:
        results = []
        for row_id, row in self.rows.items():
            if where is None or where(row):
                results.append((row_id, row))
        return results


class Database:
    def __init__(self, db_path: str = "simpledb.json"):
        self.db_path = db_path
        self.tables: Dict[str, Table] = {}
        self.load()
    
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
    
    def save(self):
        data = {
            "tables": {}
        }
        
        for table_name, table in self.tables.items():
            data["tables"][table_name] = {
                "columns": [
                    {
                        "name": col.name,
                        "data_type": col.data_type.value,
                        "primary_key": col.primary_key,
                        "unique": col.unique,
                        "nullable": col.nullable
                    }
                    for col in table.columns.values()
                ],
                "rows": {str(k): v for k, v in table.rows.items()},
                "next_id": table.next_id
            }
        
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self):
        if not os.path.exists(self.db_path):
            return
        
        with open(self.db_path, 'r') as f:
            data = json.load(f)
        
        for table_name, table_data in data.get("tables", {}).items():
            columns = [
                Column(
                    name=col["name"],
                    data_type=DataType(col["data_type"]),
                    primary_key=col.get("primary_key", False),
                    unique=col.get("unique", False),
                    nullable=col.get("nullable", True)
                )
                for col in table_data["columns"]
            ]
            
            table = Table(table_name, columns)
            table.next_id = table_data.get("next_id", 0)
            
            # Restore rows
            for row_id_str, row in table_data.get("rows", {}).items():
                row_id = int(row_id_str)
                table.rows[row_id] = row
                
                # Rebuild indexes
                for col_name, index in table.indexes.items():
                    if col_name in row and row[col_name] is not None:
                        index.add(row[col_name], row_id)
            
            self.tables[table_name] = table


class SQLParser:
    @staticmethod
    def parse_create_table(sql: str) -> Tuple[str, List[Column]]:
        # CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT UNIQUE, age INTEGER)
        # Clean up the SQL - remove extra whitespace and newlines
        sql = ' '.join(sql.split())
        match = re.match(r'CREATE TABLE (\w+)\s*\((.*)\)', sql, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError("Invalid CREATE TABLE syntax")
        
        table_name = match.group(1)
        columns_str = match.group(2)
        
        columns = []
        for col_def in columns_str.split(','):
            parts = col_def.strip().split()
            if len(parts) < 2:
                raise ValueError(f"Invalid column definition: {col_def}")
            
            col_name = parts[0]
            col_type = DataType(parts[1].upper())
            primary_key = 'PRIMARY' in [p.upper() for p in parts]
            unique = 'UNIQUE' in [p.upper() for p in parts]
            nullable = 'NOT NULL' not in col_def.upper()
            
            columns.append(Column(col_name, col_type, primary_key, unique, nullable))
        
        return table_name, columns
    
    @staticmethod
    def parse_insert(sql: str) -> Tuple[str, Dict[str, Any]]:
        # INSERT INTO users (name, age) VALUES ('Alice', 30)
        # Clean up the SQL
        sql = ' '.join(sql.split())
        match = re.match(r'INSERT INTO (\w+)\s*\((.*?)\)\s*VALUES\s*\((.*?)\)', sql, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError("Invalid INSERT syntax")
        
        table_name = match.group(1)
        columns = [c.strip() for c in match.group(2).split(',')]
        values_str = match.group(3)
        
        # Parse values (simple parser, handles strings and numbers)
        values = []
        current = ""
        in_string = False
        
        for char in values_str:
            if char == "'" and (not current or current[-1] != '\\'):
                in_string = not in_string
            elif char == ',' and not in_string:
                values.append(current.strip().strip("'"))
                current = ""
            else:
                current += char
        
        if current:
            values.append(current.strip().strip("'"))
        
        if len(columns) != len(values):
            raise ValueError("Column count doesn't match value count")
        
        # Convert values
        row = {}
        for col, val in zip(columns, values):
            if val.upper() == 'NULL':
                row[col] = None
            elif val.upper() in ('TRUE', 'FALSE'):
                row[col] = val.upper() == 'TRUE'
            else:
                try:
                    row[col] = int(val)
                except ValueError:
                    try:
                        row[col] = float(val)
                    except ValueError:
                        row[col] = val
        
        return table_name, row
    
    @staticmethod
    def parse_select(sql: str) -> Tuple[str, Optional[str]]:
        # SELECT * FROM users WHERE age > 25
        # Clean up the SQL
        sql = ' '.join(sql.split())
        match = re.match(r'SELECT \* FROM (\w+)(?:\s+WHERE\s+(.+))?', sql, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError("Invalid SELECT syntax")
        
        return match.group(1), match.group(2)
    
    @staticmethod
    def parse_update(sql: str) -> Tuple[str, Dict[str, Any], Optional[str]]:
        # UPDATE users SET age = 31 WHERE name = 'Alice'
        # Clean up the SQL
        sql = ' '.join(sql.split())
        match = re.match(r'UPDATE (\w+)\s+SET\s+(.+?)(?:\s+WHERE\s+(.+))?
        
        table_name = match.group(1)
        set_clause = match.group(2)
        where_clause = match.group(3)
        
        updates = {}
        for assignment in set_clause.split(','):
            col, val = assignment.split('=')
            col = col.strip()
            val = val.strip().strip("'")
            
            if val.upper() == 'NULL':
                updates[col] = None
            else:
                try:
                    updates[col] = int(val)
                except ValueError:
                    try:
                        updates[col] = float(val)
                    except ValueError:
                        updates[col] = val
        
        return table_name, updates, where_clause


class SimpleRDBMS:
    def __init__(self, db_path: str = "simpledb.json"):
        self.db = Database(db_path)
    
    def execute(self, sql: str) -> Any:
        sql = sql.strip()
        
        if sql.upper().startswith('CREATE TABLE'):
            table_name, columns = SQLParser.parse_create_table(sql)
            self.db.create_table(table_name, columns)
            self.db.save()
            return f"Table {table_name} created"
        
        elif sql.upper().startswith('DROP TABLE'):
            table_name = sql.split()[2]
            self.db.drop_table(table_name)
            self.db.save()
            return f"Table {table_name} dropped"
        
        elif sql.upper().startswith('INSERT INTO'):
            table_name, row = SQLParser.parse_insert(sql)
            table = self.db.get_table(table_name)
            row_id = table.insert(row)
            self.db.save()
            return f"Inserted row with ID {row_id}"
        
        elif sql.upper().startswith('SELECT'):
            table_name, where_clause = SQLParser.parse_select(sql)
            table = self.db.get_table(table_name)
            
            if where_clause:
                where_func = self._compile_where(where_clause)
                results = table.select(where_func)
            else:
                results = table.select()
            
            return results
        
        elif sql.upper().startswith('UPDATE'):
            table_name, updates, where_clause = SQLParser.parse_update(sql)
            table = self.db.get_table(table_name)
            
            if where_clause:
                where_func = self._compile_where(where_clause)
                rows = table.select(where_func)
            else:
                rows = table.select()
            
            count = 0
            for row_id, _ in rows:
                table.update(row_id, updates)
                count += 1
            
            self.db.save()
            return f"Updated {count} rows"
        
        elif sql.upper().startswith('DELETE FROM'):
            match = re.match(r'DELETE FROM (\w+)(?:\s+WHERE\s+(.+))?', sql, re.IGNORECASE)
            if not match:
                raise ValueError("Invalid DELETE syntax")
            
            table_name = match.group(1)
            where_clause = match.group(2)
            table = self.db.get_table(table_name)
            
            if where_clause:
                where_func = self._compile_where(where_clause)
                rows = table.select(where_func)
            else:
                rows = table.select()
            
            count = 0
            for row_id, _ in rows:
                table.delete(row_id)
                count += 1
            
            self.db.save()
            return f"Deleted {count} rows"
        
        else:
            raise ValueError(f"Unsupported SQL command: {sql}")
    
    def _compile_where(self, where_clause: str) -> callable:
        # Simple WHERE clause compiler (supports basic comparisons)
        def where_func(row):
            # Replace column names with row values
            expr = where_clause
            for col_name in row.keys():
                if col_name in expr:
                    val = row[col_name]
                    if isinstance(val, str):
                        expr = expr.replace(col_name, f"'{val}'")
                    else:
                        expr = expr.replace(col_name, str(val))
            
            try:
                return eval(expr)
            except:
                return False
        
        return where_func
    
    def repl(self):
        print("SimpleRDBMS Interactive Shell")
        print("Type 'exit' or 'quit' to exit")
        print("=" * 50)
        
        while True:
            try:
                sql = input("simpledb> ").strip()
                
                if sql.lower() in ('exit', 'quit'):
                    break
                
                if not sql:
                    continue
                
                result = self.execute(sql)
                
                if isinstance(result, list):
                    if not result:
                        print("No rows returned")
                    else:
                        for row_id, row in result:
                            print(f"ID {row_id}: {row}")
                else:
                    print(result)
                
            except Exception as e:
                print(f"Error: {e}")
        
        print("Goodbye!")


if __name__ == "__main__":
    rdbms = SimpleRDBMS()
    rdbms.repl()
, sql, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError("Invalid UPDATE syntax")
        
        table_name = match.group(1)
        set_clause = match.group(2)
        where_clause = match.group(3)
        
        updates = {}
        for assignment in set_clause.split(','):
            col, val = assignment.split('=')
            col = col.strip()
            val = val.strip().strip("'")
            
            if val.upper() == 'NULL':
                updates[col] = None
            else:
                try:
                    updates[col] = int(val)
                except ValueError:
                    try:
                        updates[col] = float(val)
                    except ValueError:
                        updates[col] = val
        
        return table_name, updates, where_clause


class SimpleRDBMS:
    def __init__(self, db_path: str = "simpledb.json"):
        self.db = Database(db_path)
    
    def execute(self, sql: str) -> Any:
        sql = sql.strip()
        
        if sql.upper().startswith('CREATE TABLE'):
            table_name, columns = SQLParser.parse_create_table(sql)
            self.db.create_table(table_name, columns)
            self.db.save()
            return f"Table {table_name} created"
        
        elif sql.upper().startswith('DROP TABLE'):
            table_name = sql.split()[2]
            self.db.drop_table(table_name)
            self.db.save()
            return f"Table {table_name} dropped"
        
        elif sql.upper().startswith('INSERT INTO'):
            table_name, row = SQLParser.parse_insert(sql)
            table = self.db.get_table(table_name)
            row_id = table.insert(row)
            self.db.save()
            return f"Inserted row with ID {row_id}"
        
        elif sql.upper().startswith('SELECT'):
            table_name, where_clause = SQLParser.parse_select(sql)
            table = self.db.get_table(table_name)
            
            if where_clause:
                where_func = self._compile_where(where_clause)
                results = table.select(where_func)
            else:
                results = table.select()
            
            return results
        
        elif sql.upper().startswith('UPDATE'):
            table_name, updates, where_clause = SQLParser.parse_update(sql)
            table = self.db.get_table(table_name)
            
            if where_clause:
                where_func = self._compile_where(where_clause)
                rows = table.select(where_func)
            else:
                rows = table.select()
            
            count = 0
            for row_id, _ in rows:
                table.update(row_id, updates)
                count += 1
            
            self.db.save()
            return f"Updated {count} rows"
        
        elif sql.upper().startswith('DELETE FROM'):
            match = re.match(r'DELETE FROM (\w+)(?:\s+WHERE\s+(.+))?', sql, re.IGNORECASE)
            if not match:
                raise ValueError("Invalid DELETE syntax")
            
            table_name = match.group(1)
            where_clause = match.group(2)
            table = self.db.get_table(table_name)
            
            if where_clause:
                where_func = self._compile_where(where_clause)
                rows = table.select(where_func)
            else:
                rows = table.select()
            
            count = 0
            for row_id, _ in rows:
                table.delete(row_id)
                count += 1
            
            self.db.save()
            return f"Deleted {count} rows"
        
        else:
            raise ValueError(f"Unsupported SQL command: {sql}")
    
    def _compile_where(self, where_clause: str) -> callable:
        # Simple WHERE clause compiler (supports basic comparisons)
        def where_func(row):
            # Replace column names with row values
            expr = where_clause
            for col_name in row.keys():
                if col_name in expr:
                    val = row[col_name]
                    if isinstance(val, str):
                        expr = expr.replace(col_name, f"'{val}'")
                    else:
                        expr = expr.replace(col_name, str(val))
            
            try:
                return eval(expr)
            except:
                return False
        
        return where_func
    
    def repl(self):
        print("SimpleRDBMS Interactive Shell")
        print("Type 'exit' or 'quit' to exit")
        print("=" * 50)
        
        while True:
            try:
                sql = input("simpledb> ").strip()
                
                if sql.lower() in ('exit', 'quit'):
                    break
                
                if not sql:
                    continue
                
                result = self.execute(sql)
                
                if isinstance(result, list):
                    if not result:
                        print("No rows returned")
                    else:
                        for row_id, row in result:
                            print(f"ID {row_id}: {row}")
                else:
                    print(result)
                
            except Exception as e:
                print(f"Error: {e}")
        
        print("Goodbye!")


if __name__ == "__main__":
    rdbms = SimpleRDBMS()
    rdbms.repl()