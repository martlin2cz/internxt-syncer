from typing import Union

import logging

from caches import CACHE_LOGGER_NAME, SQLITE_HELPER_LOGGER_NAME
from internxt_cli_wrapper import CLOUD_LOGGER_NAME, INTXT_CLI_WRAPPER_LOGGER_NAME
from local_filesystem import LOCAL_FILESYSTEM_LOGGER_NAME

LOGIC_LOGGERS = [CACHE_LOGGER_NAME, CLOUD_LOGGER_NAME]
HELPER_LOGGERS = [SQLITE_HELPER_LOGGER_NAME, LOCAL_FILESYSTEM_LOGGER_NAME, INTXT_CLI_WRAPPER_LOGGER_NAME]

LOGIC_LOGGER_LEVELS = {"": logging.INFO, "silent": logging.WARNING, "verbose": logging.DEBUG, "debug": logging.DEBUG}
HELPER_LOGGER_LEVELS = {"": logging.WARNING, "silent": logging.ERROR, "verbose": logging.INFO, "debug": logging.DEBUG}


def configure_logger(logger: logging.Logger, logger_level: int, kind: Union['logic', 'helper']):
    if kind == 'logic':
        formatter = logging.Formatter('%(asctime)s  %(name)8.8s %(levelname)5s - %(message)s')
    if kind == 'helper':
        formatter = logging.Formatter('%(asctime)s  %(name)8.8s %(levelname)5s -   [%(message)s]')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("syncer.log")
    file_handler.setFormatter(formatter)

    logger.setLevel(logger_level)
    #print(f"Setting level of {logger} to {logger_level}")

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def configure_logging(verbocity: str = ""):
    if verbocity not in LOGIC_LOGGER_LEVELS:
        raise ValueError(f"Invalid verbocity. Use one of {LOGIC_LOGGER_LEVELS.keys()!s}")

    root_logger = logging.getLogger()
    root_level = LOGIC_LOGGER_LEVELS[verbocity]
    configure_logger(root_logger, root_level, 'logic')

    for logger_name in LOGIC_LOGGERS:
        level = LOGIC_LOGGER_LEVELS[verbocity]
        logger = logging.getLogger(logger_name)
        configure_logger(logger, level, 'logic')

    for logger_name in HELPER_LOGGERS:
        level = HELPER_LOGGER_LEVELS[verbocity]
        logger = logging.getLogger(logger_name)
        configure_logger(logger, level, 'helper')
