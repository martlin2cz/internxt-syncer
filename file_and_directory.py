from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional


@dataclass
class Resource:
    """ The common abstract file system resource."""

    id: Optional[str]
    path: Optional[Path]


@dataclass
class File(Resource):
    """ The filesystem file. """
    pass


@dataclass
class Directory(Resource):
    """ The filesystem directory, folder. """
    pass

