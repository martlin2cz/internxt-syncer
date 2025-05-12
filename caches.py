import sqlite3
import abc

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


class SqliteCache(Cache):
    conn: sqlite3.Connection

    def __init__(self):
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        self.conn = sqlite3.connect(SQLITE_CACHE_FILE_NAME)

    def disconect(self):
        self.conn.close()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS CloudFile (
                        id TEXT PRIMARY KEY,
                        path TEXT UNIQUE
                    )
                ''')
        self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS CloudDirectory (
                        id TEXT PRIMARY KEY,
                        path TEXT UNIQUE
                    )
                ''')

    def store_file(self, file: File):
            with self.conn:
                self.conn.execute('INSERT INTO CloudFile (id, path) VALUES (?, ?)',
                                  (file.id, file.path))

    def store_directory(self, directory: Directory):
            with self.conn:
                self.conn.execute('INSERT INTO CloudDirectory (id, path) VALUES (?, ?)',
                                  (directory.id, directory.path))

    def get_file(self, path: str) -> File:
        cursor = self.conn.execute('SELECT id, path FROM CloudFile WHERE path = ?', (path,))
        row = cursor.fetchone()
        return File(*row)

    def get_directory(self, path: str) -> Directory:
        cursor = self.conn.execute('SELECT id, path FROM CloudDirectory WHERE path = ?', (path,))
        row = cursor.fetchone()
        return Directory(*row)



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
