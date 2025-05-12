import sqlite3
import abc

from file_and_directory import CloudFile, CloudDirectory

SQLITE_CACHE_FILE_NAME = "cache.sqlite"


class Cache(abc.ABC):

    def store_file(self, file: CloudFile):
        pass

    def store_directory(self, directory: CloudDirectory):
        pass

    def get_file(self, path: str) -> CloudFile:
        pass

    def get_directory(self, path: str) -> CloudDirectory:
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
                        id TEXT NOT NULL PRIMARY KEY,
                        path TEXT NOT NULL UNIQUE
                    )
                ''')
        self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS CloudDirectory (
                        id TEXT NOT NULL PRIMARY KEY,
                        path TEXT NOT NULL UNIQUE
                    )
                ''')

    def store_file(self, file: CloudFile):
            with self.conn:
                self.conn.execute('INSERT INTO CloudFile (id, path) VALUES (?, ?)',
                                  (file.id, file.path))

    def store_directory(self, directory: CloudDirectory):
            with self.conn:
                self.conn.execute('INSERT INTO CloudDirectory (id, path) VALUES (?, ?)',
                                  (directory.id, directory.path))

    def get_file(self, path: str) -> CloudFile:
        cursor = self.conn.execute('SELECT id, path FROM CloudFile WHERE path = ?', (path,))
        row = cursor.fetchone()
        return CloudFile(*row)

    def get_directory(self, path: str) -> CloudDirectory:
        cursor = self.conn.execute('SELECT id, path FROM CloudDirectory WHERE path = ?', (path,))
        row = cursor.fetchone()
        return CloudDirectory(*row)



class InMemoryCache(Cache):
    def __init__(self):
        self.files = []
        self.directories = []

    def store_file(self, file: CloudFile):
        self.files.append(file)

    def store_directory(self, directory: CloudDirectory):
        self.directories.append(directory)

    def get_file(self, path: str) -> CloudFile:
        return [file for file in self.files if file.path == path][0]

    def get_directory(self, path: str) -> CloudDirectory:
        return [directory for directory in self.directories if directory.path == path][0]
