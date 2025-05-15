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
    directories: List[str]
    files: List[str]


class InternxtCliWrapper:
    EXECUTABLE = ["node", str(Path.home().absolute()) + "/AppData/Roaming/npm/node_modules/\\@internxt/cli/bin/run.js"]
    COMMON_ARGS = ["--json", "--non-interactive"]

    def _execute(self, command_name, *command_args) -> object:
        command = self.EXECUTABLE + [command_name] + self.COMMON_ARGS + list(command_args)

        print("Executing: " + str(command))
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise IOError(f"Internxt cli failed (code: {result.returncode}): {result.stderr}")

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

    # TODO and more ...


class Cloud:
    def set_root_directory(self, dir_id: str):
        pass

    def list_directories(self, owner_dir_id: str) -> DirectoryContents:
        pass

    def create_directory(self, owner_dir_id: str, dir_name: str) -> str:
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
        directories = [fe['uuid'] for fe in response['list']['folders']]
        files = [fe['uuid'] for fe in response['list']['files']]
        return DirectoryContents(directories, files)

    def create_directory(self, owner_dir_id: str, dir_name: str) -> str:
        response = self.wrapper.create_directory(owner_dir_id, dir_name)
        return response['folder']['uuid']

    # TODO and more ...


class MockedInMemoryCloud:
    def __init__(self):
        self.previous_id = 100
        self.directories: Dict[str, List[str]] = {}
        self.files: Dict[str, List[str]] = {}

    def set_root_directory(self, dir_id: str):
        self.directories[dir_id] = []
        self.files[dir_id] = []

    def list_directories(self, owner_dir_id: str) -> DirectoryContents:
        directories = self.directories[owner_dir_id]
        files = self.files[owner_dir_id]
        return DirectoryContents(directories, files)

    def create_directory(self, owner_dir_id: str, dir_name: str) -> str:
        self.previous_id += 1
        child_dir_id = str(self.previous_id)

        self.directories[owner_dir_id].append(child_dir_id)
        self.directories[child_dir_id] = []

        return child_dir_id

    # TODO and more ...

