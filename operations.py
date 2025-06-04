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


class SimpleUpload:

    def __init__(self):
        self.filesystem = LocalFileSystem()
        self.cache = SqliteCache()
        self.cloud = InternxtCloud(self.cache)

    def upload(self, directory_path: Path, destioation_id: str):
        self.cache.store_directory_path(directory_path, destioation_id) # TODO double check server id exist
        self.cloud.set_root_directory(destioation_id)

        local_resources = self.filesystem.load(directory_path)
        for resource in local_resources:
            if resource.path == Path('.'): # litle tricky hihi
                continue

            if isinstance(resource, Directory):
                self.upload_directory(resource, destioation_id)
            if isinstance(resource, File):
                self.upload_file(resource, destioation_id)

    def upload_directory(self, directory: Directory, destination_root_id: str):
        path = directory.path

        parent_path = path.parent
        parent_id = self._mkdirs(destination_root_id, parent_path)

        dir_name = path.name
        self.cloud.create_directory(parent_id, dir_name)

    def upload_file(self, file: File, destination_root_id: str):
        path = file.path

        parent_path = path.parent
        owner_id = self._mkdirs(destination_root_id, parent_path)

        self.cloud.upload_file(owner_id, path)

    def _mkdirs(self, destination_root_id: str, a_path: Path) -> str:
        ancestor_path = a_path
        ancestor_id = self.cache.get_directory_id(a_path)
        dirs_to_create = []

        while ancestor_id is None:
            dirs_to_create.append(ancestor_path.name)

            if len(ancestor_path) <= 1:
                ancestor_id = destination_root_id
            else:
                ancestor_path = ancestor_path.parent
                ancestor_id = self.cache.get_file_id(ancestor_path)

        last_existing_dir_id = ancestor_id
        for name in dirs_to_create:
            last_existing_dir_id = self.cloud.create_directory(last_existing_dir_id, name)

        return last_existing_dir_id

