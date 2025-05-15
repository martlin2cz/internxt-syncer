from dataclasses import dataclass
import os
from typing import Optional


@dataclass
class Resource:
    """ The common abstract file system resource."""

    id: Optional[str]
    path: Optional[os.path]


@dataclass
class File(Resource):
    """ The filesystem file. """
    pass


@dataclass
class Directory(Resource):
    """ The filesystem directory, folder. """
    pass

