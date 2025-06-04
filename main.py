import logging

import argparse
from configure_logging import configure_logger

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


