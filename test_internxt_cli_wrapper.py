import io
import sys
import shutil
import tempfile
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase

from caches import InMemoryCache
from configure_logging import configure_logging
from internxt_cli_wrapper import InternxtCliWrapper, InternxtCloud, MockedInMemoryCloud

TESTING_ROOT_DIR_ID = "d0ed08d0-3e88-461b-9e67-13befc4f0e89"
TESTING_FILE_ID = "b9857eb9-9397-4cdd-aeed-54d519e330fe"

configure_logging("debug")


class TestInternxtCliWrapper(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.wrapper = InternxtCliWrapper()

    def test_list_directories_in(self):
        result = self.wrapper.list_directories_in(TESTING_ROOT_DIR_ID)
        print(result)

    def test_create_directory(self):
        result = self.wrapper.create_directory(TESTING_ROOT_DIR_ID, "foo-16")
        print(result)

    def test_upload_file(self):
        file = NamedTemporaryFile(prefix="internxt-wrapper-upload").name
        shutil.copyfile(__file__, file)
        result = self.wrapper.upload_file(TESTING_ROOT_DIR_ID, Path(file))
        print(result)

    def test_download_file(self):
        destination_directory = tempfile.mkdtemp(prefix="internxt-wrapper-download")
        result = self.wrapper.download_file(TESTING_FILE_ID, Path(destination_directory), False)
        print(result)


class TestInternxtCloud(TestCase):

    @classmethod
    def setUpClass(cls):
        cache = InMemoryCache()
        cls.cloud = InternxtCloud(cache)
        cls.cloud.set_root_directory(TESTING_ROOT_DIR_ID)

    def test_list_directories(self):
        contents = self.cloud.list_directory(TESTING_ROOT_DIR_ID)
        print(contents)
        self.assertTrue(len(contents.directories) > 0)

    def test_create_directory(self):
        dir_id = self.cloud.create_directory(TESTING_ROOT_DIR_ID, "bar-15")
        print(dir_id)
        self.assertIsNotNone(dir_id)

    def test_upload_file(self):
        file = NamedTemporaryFile(prefix="internxt-cloud-upload").name
        shutil.copyfile(__file__, file)
        file_id = self.cloud.upload_file(TESTING_ROOT_DIR_ID, Path(file))
        print(file_id)
        self.assertIsNotNone(file_id)

    def test_download_file(self):
        destination_directory = tempfile.mkdtemp(prefix="internxt-cloud-download")
        path = self.cloud.download_file(TESTING_FILE_ID, Path(destination_directory))
        print(path)



class TestMockedInMemoryCloud(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cloud = MockedInMemoryCloud()

        cls.root_dir_id = "4200"
        cls.cloud.set_root_directory(cls.root_dir_id)

    def test_1_create_directory(self):
        dir_id = self.cloud.create_directory(self.root_dir_id, "baz-15")
        print(dir_id)
        self.assertIsNotNone(dir_id)

    def test_2_upload_file(self):
        file = NamedTemporaryFile(prefix="inmemory-cloud.upload").name
        file_id = self.cloud.upload_file(self.root_dir_id, Path(file))
        print(file_id)
        self.assertIsNotNone(file_id)

    def test_3_list_directories(self):
        contents = self.cloud.list_directories(self.root_dir_id)
        print(contents)
        self.assertTrue(len(contents.directories) > 0)

    def test_4_download_file(self):
        destination_directory = (tempfile.mkdtemp(prefix="inmemory-cloud-download"))
        file_id = list(self.cloud.files_names.keys())[0]
        path = self.cloud.download_file(file_id, Path(destination_directory))
        print(path)


if __name__ == '__main__':
    unittest.main()

