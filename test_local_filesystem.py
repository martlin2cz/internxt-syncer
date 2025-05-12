from unittest import TestCase
from os import path

from file_and_directory import CloudDirectory, CloudFile
from local_filesystem import LocalFileSystem


class TestLocalFileSystem(TestCase):
    def test_load(self):
        fs = LocalFileSystem()
        actual_resources = fs.load("testing_root")
        expected_resources = [
            CloudDirectory(None, "testing_root"),
            CloudFile(None, path.join("testing_root","testing_lorem_file.txt")),
            CloudDirectory(None, path.join("testing_root", "testing_foo_dir")),
            CloudFile(None, path.join("testing_root","testing_foo_dir","testing_ipsum_file.txt"))
        ]

        self.assertEqual(expected_resources, actual_resources)


