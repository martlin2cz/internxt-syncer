<<<<<<< HEAD
import logging

import argparse
from pathlib import Path
from configure_logging import configure_logger


from operations import CacheUpdate

ROOT_DIR_ID = "f3f79de4-0895-43e5-81ef-9ae91b19254c"
ROOT_DIR_PATH = Path(".")


def construct_parser():
    parser = argparse.ArgumentParser(description="The internxt synchronizer. Sort of.")

    group = parser.add_argument_group('verbosity')
    group.add_argument("-s", "--silent", action="store_const", const="silent", dest="verbosity", help="Silent mode (only errors and warnings)")
    group.add_argument("-v", "--verbose", action="store_const", const="verbose", dest="verbosity", help="Verbose mode (detailed information)")
    group.add_argument("-d", "--debug", action="store_const", const="debug", dest="verbosity", help="Debug mode (full debug data)")

    return parser


def main():
    parser = construct_parser()
    args = parser.parse_args()

    configure_logger(args.verbocity)

    cache_update = CacheUpdate()
    cache_update.update(ROOT_DIR_ID)


=======
from pathlib import Path

from operations import CacheUpdate, SimpleUpload

ROOT_DIR_ID = "f3f79de4-0895-43e5-81ef-9ae91b19254c"
ROOT_DIR_PATH = Path(".")

if __name__ == '__main__':
    cache_update = CacheUpdate()
    cache_update.update(ROOT_DIR_ID)

    upload = SimpleUpload()
    upload.upload(ROOT_DIR_PATH, ROOT_DIR_ID)
>>>>>>> Initial uploader (not owrking)
