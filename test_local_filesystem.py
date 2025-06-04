from unittest import TestCase
from os import path

from configure_logging import configure_logging
from file_and_directory import Directory, File
from local_filesystem import LocalFileSystem

configure_logging("debug")

class TestLocalFileSystem(TestCase):
    def test_load(self):
        fs = LocalFileSystem()
        actual_resources = fs.load("testing_root")
        expected_resources = [
            Directory(None, "testing_root"),
            File(None, path.join("testing_root", "testing_lorem_file.txt")),
            Directory(None, path.join("testing_root", "testing_foo_dir")),
            File(None, path.join("testing_root", "testing_foo_dir", "testing_ipsum_file.txt"))
        ]

        self.assertEqual(expected_resources, actual_resources)


