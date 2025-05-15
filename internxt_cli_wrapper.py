import sys
import subprocess
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from caches import Cache
from file_and_directory import File, Directory


@dataclass(frozen=True)
class DirectoryContents:
    directories: Dict[str, str]
    files: Dict[str, str]


class InternxtCliWrapper:
    EXECUTABLE = ["node", str(Path.home().absolute()) + "/AppData/Roaming/npm/node_modules/\\@internxt/cli/bin/run.js"]
    COMMON_ARGS = ["--json", "--non-interactive"]

    def _execute(self, command_name, *command_args) -> object:
        command = self.EXECUTABLE + [command_name] + self.COMMON_ARGS + list(command_args)

        print("Executing: " + str(command))
        result = subprocess.run(command, capture_output=True, text=True)
        #if result.returncode != 0:
        #    raise IOError(f"Internxt cli failed (code: {result.returncode})")

        try:
            jsoned = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise IOError(f"Failed to parse Internxt cli output: {e}")

        if 'success' not in jsoned or not jsoned['success']:
            message = jsoned['message'] if 'message' in jsoned else "[unspecified]"
            raise IOError(f"The command {command_name} responded with no-success: {message}")

        return jsoned

    def list_directories_in(self, owner_dir_id: str) -> object:
        return self._execute("list", "--id", owner_dir_id)

    def create_directory(self, owner_dir_id: str, dir_name: str) -> object:
        return self._execute("create-folder", "--id", owner_dir_id, "--name", dir_name)

    def upload_file(self, owner_dir_id: str, file_path: Path) -> object:
        return self._execute("upload-file", "--destination", owner_dir_id, "--file", file_path)

    def download_file(self, file_id: str, destination_directory_path: Path, override: bool) -> object:
        if override:
            return self._execute("download-file", "--directory", destination_directory_path, "--id", file_id, "--override")
        else:
            return self._execute("download-file", "--directory", destination_directory_path, "--id", file_id)


    # TODO and more ...


class Cloud:
    def set_root_directory(self, dir_id: str):
        pass

    def list_directories(self, owner_dir_id: str) -> DirectoryContents:
        pass

    def create_directory(self, owner_dir_id: str, dir_name: str) -> str:
        pass

    def upload_file(self, owner_dir_id: str, file_path: Path) -> str:
        pass

    def download_file(self, file_id: str, destination_directory_path: Path) -> Path:
        pass

    # TODO and more ...


class InternxtCloud(Cloud):

    def __init__(self, cache: Cache):
        self.wrapper = InternxtCliWrapper()
        self.cache = cache

    def set_root_directory(self, dir_id: str):
        pass

    def list_directories(self, owner_dir_id: str) -> DirectoryContents:
        response = self.wrapper.list_directories_in(owner_dir_id)
        directories = {fe['uuid']: self.file_name(fe, 'plainName', None) for fe in response['list']['folders']}
        files = {fe['uuid']: self.file_name(fe, 'plainName', 'type') for fe in response['list']['files']}
        return DirectoryContents(directories, files)

    def create_directory(self, owner_dir_id: str, dir_name: str) -> str:
        response = self.wrapper.create_directory(owner_dir_id, dir_name)
        return response['folder']['uuid']

    def upload_file(self, owner_dir_id: str, file_path: Path) -> str:
        response = self.wrapper.upload_file(owner_dir_id, file_path)
        return response['file']['uuid']

    def download_file(self, file_id: str, destination_directory_path: Path) -> Path:
        response = self.wrapper.download_file(file_id, destination_directory_path, False)
        name = self.file_name(response['file'], 'name', 'type')
        return Path(destination_directory_path, name)

    # TODO and more ...
    @classmethod
    def file_name(cls, file_object: object, base_name_key: str, extension_key: str | None):
        base_name = file_object[base_name_key] if base_name_key else None
        extension = file_object[extension_key] if extension_key else None
        if extension is None:
            return base_name
        else:
            return f"{base_name}.{extension}"



class MockedInMemoryCloud:
    def __init__(self):
        self.previous_id = 100
        self.directories_names: Dict[str, str] = {}
        self.files_names: Dict[str, str] = {}
        self.directories_child_dirs: Dict[str, List[str]] = {}
        self.directories_child_files: Dict[str, List[str]] = {}

    def set_root_directory(self, dir_id: str):
        self.directories_names[dir_id] = "" # we don't care about the root dir name
        self.directories_child_dirs[dir_id] = []
        self.directories_child_files[dir_id] = []

    def list_directories(self, owner_dir_id: str) -> DirectoryContents:
        directories_ids = self.directories_child_dirs[owner_dir_id]
        files_ids = self.directories_child_files[owner_dir_id]

        directories = {did: self.directories_names[did] for did in directories_ids}
        files = {fid: self.files_names[fid] for fid in files_ids}

        return DirectoryContents(directories, files)

    def create_directory(self, owner_dir_id: str, dir_name: str) -> str:
        self.previous_id += 1
        child_dir_id = str(self.previous_id)

        self.directories_child_dirs[owner_dir_id].append(child_dir_id)

        self.directories_names[child_dir_id] = dir_name
        self.directories_child_dirs[child_dir_id] = []
        self.directories_child_files[child_dir_id] = []

        return child_dir_id

    def upload_file(self, owner_dir_id: str, file_path: Path) -> str:
        self.previous_id += 1
        new_file_id = str(self.previous_id)

        self.files_names[new_file_id] = file_path.name
        self.directories_child_files[owner_dir_id].append(new_file_id)
        return new_file_id

    def download_file(self, file_id: str, destination_directory_path: Path) -> Path:
        file_name = self.files_names[file_id]
        destination_path = Path(destination_directory_path, file_name)
        fake_contents = f"{file_id}={file_name}"

        with open(destination_path, "w") as handle:
            handle.write(fake_contents)

        return Path(destination_directory_path, file_name)

    # TODO and more ...

    def __str__(self):
        return f"[directories={self.directories}, files={self.files}]"


