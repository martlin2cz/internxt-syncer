from dataclasses import dataclass
import os
from typing import Optional

@dataclass
class Resource:
    id: Optional[str]
    path: Optional[os.path]

@dataclass
class File(Resource):
    pass

@dataclass
class Directory(Resource):
    pass

