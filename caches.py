import dataclasses
import sqlite3
import abc
from pathlib import Path
from typing import Dict, List, Union, Tuple

import logging

from file_and_directory import File, Directory

SQLITE_CACHE_FILE_NAME = "cache.sqlite"

# logging
CACHE_LOGGER_NAME = "cache"
cache_logger = logging.getLogger(CACHE_LOGGER_NAME)

SQLITE_HELPER_LOGGER_NAME = "sqlhelper"
sqlite_logger = logging.getLogger(SQLITE_HELPER_LOGGER_NAME)


class Cache(abc.ABC):
    """
    The cache of the directories and files in the cloud.
    """

    def store_file_id(self, file_path: Path, file_id: str):
        """ Saves the id of the file identified by the path. """
        pass

    def store_file_path(self, file_path: Path, file_id: str):
        """ Saves the path of the file identified by the id. """
        pass

    def store_directory_id(self, directory_path: Path, directory_id: str):
        """ Saves the id of the directory identified by the path. """
        pass

    def store_directory_path(self, directory_path: Path, directory_id: str):
        """ Saves the path of the file identified by the id. """
        pass

    def get_file_id(self, file_path: Path) -> str:
        """ Retrieves the id of the file with the specified path. """
        pass

    def get_file_path(self, file_id: str) -> Path:
        """ Retrieves the path of the file with the specified id. """
        pass

    def get_directory_id(self, directory_path: Path) -> str:
        """ Retrieves the id of the directory with the specified path. """
        pass

    def get_directory_path(self, directory_id: str) -> Path:
        """ Retrieves the path of the directory with the specified id. """
        pass


class SqliteTableHelper:
    """ The helper tool for the sqlite table manipulation. Encapsulates the SQL quering by nicer convience methods. """

    conn: sqlite3.Connection
    table_name: str

    def __init__(self, connection: sqlite3.Connection, table_name: str, table_def: Dict[str, str]):
        """ Creates the helper for the sqlite3 connection, working with table with given name and attributes. """
        self.conn = connection

        self.table_name = table_name
        self.table_columns_names = tuple(table_def.keys())

        self.create_table(table_def)

    def create_table(self, table_def):
        """ Creates the table. Internal. """

        with self.conn:
            table_def_strs = [f"{col_name} {col_declaration}" for col_name, col_declaration in table_def.items()]
            table_def_str = f"({', '.join(table_def_strs)})"
            sql = f"CREATE TABLE IF NOT EXISTS  {self.table_name} {table_def_str}"
            sqlite_logger.info(f"Creating table: {sql}")
            self.conn.execute(sql)

    def insert_into(self, data: Dict[str, str]):
        """ Inserts given data into the table. """

        with self.conn:
            values = tuple(data.values())
            values_placeholders = ["?" for value in data.values()]

            columns_names_str = f"({', '.join(data.keys())})"
            values_placeholders_str = f"({', '.join(values_placeholders)})"

            sql = f"INSERT INTO {self.table_name} {columns_names_str} VALUES {values_placeholders_str}"
            sqlite_logger.info(f"Inserting: {sql} values: {values}")
            self.conn.execute(sql, values)

    def update_in(self, new_data: Dict[str, any], where_statement: str, where_values: List[any]):
        """ Updates the data in the table to the given ones based on the condition. """

        with self.conn:
            values = tuple(new_data.values())
            assigned_columns_names = new_data.keys()

            columns_assignments_strs = [f"{column_name} = ?" for column_name in assigned_columns_names]
            columns_assignments_str = f"{', '.join(columns_assignments_strs)}"

            sql = f"UPDATE {self.table_name} SET {columns_assignments_str} WHERE {where_statement}"
            sql_values = [*values, *where_values]
            sqlite_logger.info(f"Updating: {sql} values {sql_values}")
            self.conn.execute(sql, sql_values)

    def select_from(self, where_statement: str = None, where_values: List[any] = None) -> List[Dict[str, any]]:
        """ Selects the records from the table (optionally only those matcing the criteria). """

        with self.conn:
            cursor = self._do_select(where_statement, where_values)
            return [self._tuple_to_dict(record) for record in cursor.fetchall()]

    def select_one(self, where_statement: str = None, where_values: List[any] = None):
        """ Retrieves one and only one record form the table. """
        with self.conn:
            cursor = self._do_select(where_statement, where_values)
            fetched = cursor.fetchmany(2)
            if len(fetched) == 0:
                return None
            elif len(fetched) == 1:
                return self._tuple_to_dict(fetched[0])
            else:
                raise ValueError("Not one record matching: " + str(fetched))

    def _do_select(self, where_statement, where_values):
        columns_str = f"{', '.join(self.table_columns_names)}"

        if where_statement is None:
            sql = f"SELECT {columns_str} FROM {self.table_name}"
            sqlite_logger.info(f"Selecting: {sql}")
            return self.conn.execute(sql)
        else:
            args = where_values if where_values is not None else []
            sql = f"SELECT {columns_str} FROM {self.table_name} WHERE {where_statement}"
            sqlite_logger.info(f"Selecting: {sql}, args: {args}")
            return self.conn.execute(sql, args)

    def _tuple_to_dict(self, values: Tuple[any]):
        if values is None:
            return None
        else:
            return {column_name: values[i] for i, column_name in enumerate(self.table_columns_names)}


class SqliteCache(Cache):
    """ The implementation of Cache, which stores persistently into the sqlite3 database. """

    def __init__(self):
        self.conn = sqlite3.connect(SQLITE_CACHE_FILE_NAME)
        self.fileTableHelper = SqliteTableHelper(self.conn, "File", {
            "id": "TEXT",
            "path": "TEXT"
        })
        self.directoryTableHelper = SqliteTableHelper(self.conn, "Directory", {
            "id": "TEXT",
            "path": "TEXT"
        })

    def disconect(self):
        self.conn.close()

    def _create_or_update(self, helper: SqliteTableHelper, condition_colum: str, condition_value: any, set_column: str, set_value: any):
        where = f"{condition_colum} = ?"
        where_values = [condition_value]
        existing_record = helper.select_one(where, where_values)

        if existing_record:
            update_data = {set_column: set_value}
            cache_logger.debug(f"Setting {update_data} where {where} is {where_values}")
            helper.update_in(update_data, where, where_values)
        else:
            insert_data = {condition_colum: condition_value, set_column: set_value}
            cache_logger.debug(f"Creating {insert_data}")
            helper.insert_into(insert_data)

    def _get_value(self, helper: SqliteTableHelper, condition_colum: str, condition_value: any, get_column: str):
        where = f"{condition_colum} = ?"
        where_values = [condition_value]
        record = helper.select_one(where, where_values)

        if record:
            return record[get_column]
        else:
            return None

    def store_file_id(self, file_path: Path, file_id: str):
        cache_logger.info(f"Storing file id {file_id} for path {file_path}")
        self._create_or_update(self.fileTableHelper, 'path', str(file_path), 'id', file_id)

    def store_file_path(self, file_path: Path, file_id: str):
        cache_logger.info(f"Storing file path {file_path} for id {file_id}")
        self._create_or_update(self.fileTableHelper, 'id', file_id,'path', str(file_path))

    def store_directory_id(self, directory_path: Path, directory_id: str):
        cache_logger.info(f"Storing directory id {directory_id} for path {directory_path}")
        self._create_or_update(self.directoryTableHelper, 'path', str(directory_path), 'id', directory_id)

    def store_directory_path(self, directory_path: Path, directory_id: str):
        cache_logger.info(f"Storing file path {directory_path} for id {directory_id}")
        self._create_or_update(self.directoryTableHelper,  'id', directory_id,'path', str(directory_path))

    def get_file_id(self, file_path: Path) -> str:
        cache_logger.info(f"Getting file id for path {file_path}")
        return self._get_value(self.fileTableHelper, 'path', str(file_path), 'id')

    def get_file_path(self, file_id: str) -> Path:
        cache_logger.info(f"Getting file path for path {file_id}")
        return Path(self._get_value(self.fileTableHelper, 'id', file_id, 'path'))

    def get_directory_id(self, directory_path: Path) -> str:
        cache_logger.info(f"Getting directory id for path {directory_path}")
        return self._get_value(self.directoryTableHelper, 'path', str(directory_path), 'id')

    def get_directory_path(self, directory_id: str) -> Path:
        cache_logger.info(f"Getting directory path for path {directory_id}")
        return Path(self._get_value(self.directoryTableHelper, 'id', directory_id, 'path'))


class InMemoryCache(Cache):
    """ The In-Memory implementation of the cache. """

    def __init__(self):
        self.files_ids = {}
        self.files_paths = {}
        self.directories_ids = {}
        self.directories_paths = {}

    def store_file_id(self, file_path: Path, file_id: str):
        cache_logger.info(f"Storing file id {file_id} for path {file_path}")
        self.files_ids[str(file_path)] = file_id

    def store_file_path(self, file_path: Path, file_id: str):
        cache_logger.info(f"Storing file path {file_path} for id {file_id}")
        self.files_paths[file_id] = str(file_path)

    def store_directory_id(self, directory_path: Path, directory_id: str):
        cache_logger.info(f"Storing directory id {directory_id} for path {directory_path}")
        self.directories_ids[str(directory_path)] = directory_id

    def store_directory_path(self, directory_path: Path, directory_id: str):
        cache_logger.info(f"Storing file path {directory_path} for id {directory_id}")
        self.directories_paths[directory_id] = str(directory_path)

    def get_file_id(self, file_path: Path) -> str:
        cache_logger.info(f"Getting file id for path {file_path}")
        return self.files_ids[str(file_path)]

    def get_file_path(self, file_id: str) -> Path:
        cache_logger.info(f"Getting file path for path {file_id}")
        return Path(self.files_paths[file_id])

    def get_directory_id(self, directory_path: Path) -> str:
        cache_logger.info(f"Getting directory id for path {directory_path}")
        return self.directories_ids[str(directory_path)]

    def get_directory_path(self, directory_id: str) -> Path:
        cache_logger.info(f"Getting directory path for path {directory_id}")
        return Path(self.directories_paths[directory_id])
