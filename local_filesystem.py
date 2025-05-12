from typing import Union, List
import os

from file_and_directory import Directory, File


class LocalFileSystem:
    def load(self, root: os.path) -> List[Union[File, Directory]]:
        result = []
        for (root,dirs,files) in os.walk(root):
            dir_path = root
            dir_id = None

            directory = Directory(dir_id, dir_path)
            result.append(directory)

            for file in files:
                file_path = os.path.join(root, file)
                file_id = None

                file = File(file_id, file_path)
                result.append(file)

        return result