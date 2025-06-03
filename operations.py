from pathlib import Path

from file_and_directory import Directory, File
from local_filesystem import LocalFileSystem
from caches import SqliteCache
from internxt_cli_wrapper import InternxtCloud

class CacheUpdate:
    def __init__(self):
        self.cache = SqliteCache()
        self.cloud = InternxtCloud(self.cache)

    def update(self, root_dir_id: str):
        root_dir_path = Path(".")
        self.cache.store_directory_id(root_dir_path, root_dir_id)

        current_path = Path(".")
        self.update_directory(root_dir_id, current_path)

    def update_directory(self, directory_id: str, current_path: Path):
        contents = self.cloud.list_directory(directory_id)
        for directory_id, directory_name in contents.directories.items():
            directory_path = Path(current_path, directory_name)
            self.cache.store_directory_id(directory_path, directory_id)

            self.update_directory(directory_id, directory_path)

        for file_id, file_name in contents.files.items():
            file_path = Path(current_path, file_name)
            self.cache.store_file_id(file_path, file_id)



