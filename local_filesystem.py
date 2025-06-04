from typing import Union, List
import os

import logging

from file_and_directory import Directory, File

LOCAL_FILESYSTEM_LOGGER_NAME = "localfs"
logger = logging.getLogger(LOCAL_FILESYSTEM_LOGGER_NAME)

class LocalFileSystem:
    def load(self, root: os.path) -> List[Union[File, Directory]]:
        logger.info(f"Loading contents of a directory {root}")
        result = []
        for (root,dirs,files) in os.walk(root):
            dir_path = root
            dir_id = None

            directory = Directory(dir_id, dir_path)
            result.append(directory)
            logger.debug(f"Found directory {dir_path}")

            for file in files:
                file_path = os.path.join(root, file)
                file_id = None

                file = File(file_id, file_path)
                result.append(file)
                logger.debug(f"Found file {file_path}")

        return result
