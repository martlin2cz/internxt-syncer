import abc
import sqlite3
import sys
import tempfile
import unittest
import os
from pathlib import Path
from unittest import TestCase

from file_and_directory import File, Directory
from caches import SqliteCache, SQLITE_CACHE_FILE_NAME, InMemoryCache, SqliteTableHelper, Cache


class AbstractCacheTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cache = cls.construct_cache_instance()

    @classmethod
    def tearDownClass(cls):
        cls.terminate_cache_instance(cls.cache)

    def test_1_store_file_id(self):
        self.cache.store_file_id(Path("foo", "bar.txt"), "111")
        self.cache.store_file_id(Path("foo", "bar.txt"), "112")

    def test_2_store_file_path(self):
        self.cache.store_file_path(Path("baz", "aux.txt"), "120")
        self.cache.store_file_path(Path("baz", "AUX.txt"), "120")

    def test_3_store_directory_id(self):
        self.cache.store_directory_id(Path("lorem", "ipsum"), "211")
        self.cache.store_directory_id(Path("lorem", "ipsum"), "212")

    def test_4_store_directory_path(self):
        self.cache.store_directory_path(Path("dolor", "sit"), "220")
        self.cache.store_directory_path(Path("dolor", "SIT"), "220")

    def test_5_get_file_id(self):
        self.assertEqual("112", self.cache.get_file_id(Path("foo", "bar.txt")))
        #self.assertEqual(None, self.cache.get_file_id(Path("whatever")))

    def test_6_get_file_path(self):
        self.assertEqual(Path("baz", "AUX.txt"), self.cache.get_file_path("120"))
        #self.assertEqual(None, self.cache.get_file_path("whatever"))

    def test_7_get_directory_id(self):
        self.assertEqual("212", self.cache.get_directory_id(Path("lorem", "ipsum")))
        #self.assertEqual(None, self.cache.get_directory_id(Path("whatever")))

    def test_8_get_directory_path(self):
        self.assertEqual(Path("dolor", "SIT"), self.cache.get_directory_path("220"))
        #self.assertEqual(None, self.cache.get_directory_path("whatever"))

    @classmethod
    def construct_cache_instance(cls) -> Cache:
        pass

    @classmethod
    def terminate_cache_instance(cls, cache: Cache):
        pass


class TestSqliteCache(AbstractCacheTestCase):
    @classmethod
    def construct_cache_instance(cls) -> SqliteCache:
        return SqliteCache()

    @classmethod
    def terminate_cache_instance(cls, cache: SqliteCache):
        cache.disconect()
        os.remove(SQLITE_CACHE_FILE_NAME)


class TestInMemoryCache(AbstractCacheTestCase):
    @classmethod
    def construct_cache_instance(cls) -> InMemoryCache:
        return InMemoryCache()

    @classmethod
    def terminate_cache_instance(cls, cache: InMemoryCache):
        pass


class TestSqliteTableHelper(unittest.TestCase):

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

            self.assertIsNone(helper.select_one("name = ?", ["DOLOR"]))

        conn.close()


del AbstractCacheTestCase

if __name__ == '__main__':
    unittest.main()
