from unittest import TestCase

from caches import InMemoryCache
from internxt_cli_wrapper import InternxtCliWrapper, InternxtCloud, MockedInMemoryCloud

TESTING_ROOT_DIR_ID = "d0ed08d0-3e88-461b-9e67-13befc4f0e89"


class TestInternxtCliWrapper(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.wrapper = InternxtCliWrapper()

    def test_list_directories_in(self):
        result = self.wrapper.list_directories_in(TESTING_ROOT_DIR_ID)
        print(result)

    def test_create_directory(self):
        result = self.wrapper.create_directory(TESTING_ROOT_DIR_ID, "foo-7")
        print(result)


class TestInternxtCloud(TestCase):

    @classmethod
    def setUpClass(cls):
        cache = InMemoryCache()
        cls.cloud = InternxtCloud(cache)
        cls.cloud.set_root_directory(TESTING_ROOT_DIR_ID)

    def test_list_directories(self):
        contents = self.cloud.list_directories(TESTING_ROOT_DIR_ID)
        print(contents)
        self.assertTrue(len(contents.directories) > 0)

    def test_create_directory(self):
        dir_id = self.cloud.create_directory(TESTING_ROOT_DIR_ID, "bar-7")
        print(dir_id)
        self.assertIsNotNone(dir_id)



class TestMockedInMemoryCloud(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cloud = MockedInMemoryCloud()

        cls.root_dir_id = "4200"
        cls.cloud.set_root_directory(cls.root_dir_id)

    def test_create_directory(self):
        dir_id = self.cloud.create_directory(self.root_dir_id, "baz-7")
        print(dir_id)
        self.assertIsNotNone(dir_id)

    def test_list_directories(self):
        contents = self.cloud.list_directories(self.root_dir_id)
        print(contents)
        self.assertTrue(len(contents.directories) > 0)


if __name__ == '__main__':
    unittest.main()

