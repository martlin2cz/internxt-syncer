from dataclasses import dataclass
import os


@dataclass
class CloudFile:
    id: str
    path: os.path


@dataclass
class CloudDirectory:
    id: str
    path: os.path

