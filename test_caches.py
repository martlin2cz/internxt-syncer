import sqlite3
import sys
import tempfile
import unittest
import os
from unittest import TestCase

from file_and_directory import File, Directory
from caches import SqliteCache, SQLITE_CACHE_FILE_NAME, InMemoryCache, SqliteTableHelper


class TestSqliteCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = SqliteCache()

    @classmethod
    def tearDownClass(cls):
        cls.cache.disconect()
        os.remove(SQLITE_CACHE_FILE_NAME)

    def test_store_and_get_file(self):
        file = File(id="42", path='/lorem/foo_file.txt')
        self.cache.store_file(file)

        retrieved_file = self.cache.get_file('/lorem/foo_file.txt')
        self.assertIsNotNone(retrieved_file)

        self.assertEqual(retrieved_file.id, file.id)
        self.assertEqual(retrieved_file.path, file.path)

    def test_store_and_get_directory(self):
        directory = Directory(id="43", path='/ipsum/bar_directory')
        self.cache.store_directory(directory)

        retrieved_directory = self.cache.get_directory('/ipsum/bar_directory')
        self.assertIsNotNone(retrieved_directory)

        self.assertEqual(retrieved_directory.id, directory.id)
        self.assertEqual(retrieved_directory.path, directory.path)


class TestInMemoryCache(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cache = InMemoryCache()

    def test_store_and_get_file(self):
        file = File(id="42", path='/lorem/foo_file.txt')
        self.cache.store_file(file)

        retrieved_file = self.cache.get_file('/lorem/foo_file.txt')
        self.assertIsNotNone(retrieved_file)

        self.assertEqual(retrieved_file.id, file.id)
        self.assertEqual(retrieved_file.path, file.path)

    def test_store_and_get_directory(self):
        directory = Directory(id="43", path='/ipsum/bar_directory')
        self.cache.store_directory(directory)

        retrieved_directory = self.cache.get_directory('/ipsum/bar_directory')
        self.assertIsNotNone(retrieved_directory)

        self.assertEqual(retrieved_directory.id, directory.id)
        self.assertEqual(retrieved_directory.path, directory.path)



class TestSqliteTableHelper(TestCase):

    def test_foo(self):
        tmp_dir = tempfile.TemporaryDirectory(prefix="foo_db_sqlite")
        file = os.path.join(tmp_dir.name, "foo.db.sqlite")
        conn = sqlite3.connect(file)
        with conn:
            helper = SqliteTableHelper(conn,"Foo", {
                "name": "TEXT",
                "number": "INTEGER"
            })

            helper.insert_into({"name": "lorem", "number": 421})
            helper.insert_into({"name": "ipsum", "number": 422})

            helper.update_in({"number": 420}, "name = ?", ["lorem"])
            helper.update_in({"name": "IPSUM"}, "name = ?", ["ipsum"])

            self.assertEqual(
            [
                    {"name": "lorem", "number": 420},
                    {"name": "IPSUM", "number": 422}
                ],
                helper.select_from())

            self.assertEqual(
            [],
                 helper.select_from("name = ?", ["ipsum"]))

            self.assertEqual({"name": "lorem", "number": 420}, helper.select_one("name = ?", ["lorem"]))

            try:
                helper.select_one("name = ?", ["DOLOR"])
            except ValueError as ex:
                self.assertTrue(ex is not None)

        conn.close()


if __name__ == '__main__':
    unittest.main()
