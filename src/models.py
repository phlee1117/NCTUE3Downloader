from typing import NamedTuple
from enum import Enum
from dataclasses import dataclass


class FolderType(Enum):
    HANDOUT = 1
    REFERENCE = 2
    ASSIGNMENT = 3


@dataclass
class E3File:
    name: str
    course_name: str
    hash_val: str
    url: str
    timemodified: int


class Folder(NamedTuple):
    folder_type: FolderType
    name: str
    folder_id: str
    course_id: str


class Course(NamedTuple):
    course_id: str
    course_name: str
