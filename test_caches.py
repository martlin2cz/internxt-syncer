import unittest
import os
from file_and_directory import CloudFile, CloudDirectory
from caches import SqliteCache, SQLITE_CACHE_FILE_NAME, InMemoryCache


class TestSqliteCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = SqliteCache()

    @classmethod
    def tearDownClass(cls):
        cls.cache.disconect()
        os.remove(SQLITE_CACHE_FILE_NAME)

    def test_store_and_get_file(self):
        file = CloudFile(id="42", path='/lorem/foo_file.txt')
        self.cache.store_file(file)

        retrieved_file = self.cache.get_file('/lorem/foo_file.txt')
        self.assertIsNotNone(retrieved_file)

        self.assertEqual(retrieved_file.id, file.id)
        self.assertEqual(retrieved_file.path, file.path)

    def test_store_and_get_directory(self):
        directory = CloudDirectory(id="43", path='/ipsum/bar_directory')
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
        file = CloudFile(id="42", path='/lorem/foo_file.txt')
        self.cache.store_file(file)

        retrieved_file = self.cache.get_file('/lorem/foo_file.txt')
        self.assertIsNotNone(retrieved_file)

        self.assertEqual(retrieved_file.id, file.id)
        self.assertEqual(retrieved_file.path, file.path)

    def test_store_and_get_directory(self):
        directory = CloudDirectory(id="43", path='/ipsum/bar_directory')
        self.cache.store_directory(directory)

        retrieved_directory = self.cache.get_directory('/ipsum/bar_directory')
        self.assertIsNotNone(retrieved_directory)

        self.assertEqual(retrieved_directory.id, directory.id)
        self.assertEqual(retrieved_directory.path, directory.path)


if __name__ == '__main__':
    unittest.main()
