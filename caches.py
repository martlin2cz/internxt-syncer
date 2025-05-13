import dataclasses
import sqlite3
import abc
from typing import Dict, List, Union, Tuple

from file_and_directory import File, Directory

SQLITE_CACHE_FILE_NAME = "cache.sqlite"


class Cache(abc.ABC):

    def store_file(self, file: File):
        pass

    def store_directory(self, directory: Directory):
        pass

    def get_file(self, path: str) -> File:
        pass

    def get_directory(self, path: str) -> Directory:
        pass


SQLITE_CACHE_FILE_NAME = "cache.sqlite3"


class SqliteTableHelper:
    conn: sqlite3.Connection
    table_name: str

    def __init__(self, connection: sqlite3.Connection, table_name: str, table_def: Dict[str, str]):
        self.conn = connection

        self.table_name = table_name
        self.table_columns_names = tuple(table_def.keys())

        self.create_table(table_def)

    def create_table(self, table_def):
        with self.conn:
            table_def_strs = [f"{col_name} {col_declaration}" for col_name, col_declaration in table_def.items()]
            table_def_str = f"({', '.join(table_def_strs)})"
            sql = f"CREATE TABLE IF NOT EXISTS  {self.table_name} {table_def_str}"
            self.conn.execute(sql)

    def insert_into(self, data: Dict[str, str]):
        with self.conn:
            values = tuple(data.values())
            values_placeholders = ["?" for value in self.table_columns_names]

            columns_names_str = f"({', '.join(self.table_columns_names)})"
            values_placeholders_str = f"({', '.join(values_placeholders)})"

            sql = f"INSERT INTO {self.table_name} {columns_names_str} VALUES {values_placeholders_str}"
            self.conn.execute(sql, values)

    def update_in(self, new_data: Dict[str, any], where_statement: str, where_values: List[any]):
        with self.conn:
            values = tuple(new_data.values())
            assigned_columns_names = new_data.keys()

            columns_assignments_strs = [f"{column_name} = ?" for column_name in assigned_columns_names]
            columns_assignments_str = f"{', '.join(columns_assignments_strs)}"

            sql = f"UPDATE {self.table_name} SET {columns_assignments_str} WHERE {where_statement}"
            sql_values = [*values, *where_values]
            self.conn.execute(sql, sql_values)

    def select_from(self, where_statement: str = None, where_values: List[any] = None):
        with self.conn:
            cursor = self._do_select(where_statement, where_values)
            return [self._tuple_to_dict(record) for record in cursor.fetchall()]

    def select_one(self, where_statement: str = None, where_values: List[any] = None):
        with self.conn:
            cursor = self._do_select(where_statement, where_values)
            fetched = cursor.fetchmany(2)
            if len(fetched) != 1:
                raise ValueError("Not one record matching: " + str(fetched))

            return self._tuple_to_dict(fetched[0])

    def _do_select(self, where_statement, where_values):
        columns_str = f"{', '.join(self.table_columns_names)}"

        if where_statement is None:
            sql = f"SELECT {columns_str} FROM {self.table_name}"
            return self.conn.execute(sql)
        else:
            args = where_values if where_values is not None else []
            sql = f"SELECT {columns_str} FROM {self.table_name} WHERE {where_statement}"
            return self.conn.execute(sql, args)

    def _tuple_to_dict(self, values: Tuple[any]):
        if values is None:
            return None
        else:
            return {column_name: values[i] for i, column_name in enumerate(self.table_columns_names)}


class SqliteCache(Cache):

    def __init__(self):
        self.conn = sqlite3.connect(SQLITE_CACHE_FILE_NAME)
        self.fileTableHelper = SqliteTableHelper(self.conn, "File", {
            "id": "TEXT PRIMARY KEY",
            "path": "TEXT UNIQUE"
        })
        self.directoryTableHelper = SqliteTableHelper(self.conn, "Directory", {
            "id": "TEXT PRIMARY KEY",
            "path": "TEXT UNIQUE"
        })

    def disconect(self):
        self.conn.close()

    def store_file(self, file: File):
        self.fileTableHelper.insert_into(file.__dict__)

    def store_directory(self, directory: Directory):
        self.directoryTableHelper.insert_into(directory.__dict__)

    def get_file(self, path: str) -> File:
        dicted = self.fileTableHelper.select_one("path = ?", [path])
        return File(**dicted)

    def get_directory(self, path: str) -> Directory:
        dicted = self.directoryTableHelper.select_one("path = ?", [path])
        return Directory(**dicted)


class InMemoryCache(Cache):
    def __init__(self):
        self.files = []
        self.directories = []

    def store_file(self, file: File):
        self.files.append(file)

    def store_directory(self, directory: Directory):
        self.directories.append(directory)

    def get_file(self, path: str) -> File:
        return [file for file in self.files if file.path == path][0]

    def get_directory(self, path: str) -> Directory:
        return [directory for directory in self.directories if directory.path == path][0]
