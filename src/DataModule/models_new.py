import base64
import functools
import gzip

import typing
from enum import Enum


def _encode_string(s: str) -> str:
    compressed = gzip.compress(str(s).encode())
    return base64.b64encode(compressed).decode()


def _decode_string(s: str) -> str:
    decoded = base64.b64decode(str(s).encode())
    return gzip.decompress(decoded).decode()


class SuperBase:
    def __init__(self):
        self._name = self.__class__.__name__

    def __repr__(self):
        return f"<{self._name}: {self.__dict__.__repr__()}>"


class Base(SuperBase):
    def __init__(self):
        super().__init__()

    def _hooks(self):
        pass

    @classmethod
    def create(cls, json):
        c = cls()
        c.__dict__.update(
            {
                key: cls._create_inner(val)
                for key, val in json.items()
                if key in c.__dict__.keys()
            }
        )
        c._hooks()
        return c

    @classmethod
    def _create_inner(cls, val):
        if isinstance(val, list):
            return [cls._create_inner(v) for v in val]
        elif isinstance(val, dict):
            if "_name" in val:
                return globals()[val["_name"]].create(val)
            return val
        else:
            return val

    def serialize(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}


class User(Base):
    def __init__(self):
        super().__init__()
        self.name = None
        self.email = None


class Commit(Base):
    def __init__(self):
        super().__init__()
        self.sha = ""
        self.message = ""
        self.author = None
        self.committer = None
        self.date = None
        self.files = []


class ChangeEnum(Enum):
    ADDED = 0
    MODIFIED = 1
    RENAMED = 2
    DELETED = 3


def ChangeEnum_fromtype(t):
    # A = Added
    # D = Deleted
    # M = Modified
    # R = Renamed
    # T = Changed in the type
    if t == 'A':
        return ChangeEnum.ADDED
    if t == 'M':
        return ChangeEnum.MODIFIED
    if t == 'D':
        return ChangeEnum.DELETED
    if t == 'R':
        return ChangeEnum.RENAMED
    raise NameError(f"type name {t} is not known")


def ChangeEnum_fromtuple(is_added, is_modified, is_removed, is_renamed):
    if is_added:
        return ChangeEnum.ADDED
    if is_removed:
        return ChangeEnum.DELETED
    if is_renamed:
        return ChangeEnum.RENAMED
    else:
        assert is_modified
        return ChangeEnum.MODIFIED


@functools.total_ordering
class FileChangeset(Base):
    def __init__(self):
        super().__init__()
        self.source = ""
        self.target = ""
        self.changetype = ChangeEnum.MODIFIED
        self.patch = None

    def __eq__(self, other):
        return self.changetype == other.changetype

    def __lt__(self, other):
        return self.changetype != other.changetype and \
               self.changetype == ChangeEnum.RENAMED

class Patch(Base):
    def __init__(self):
        super().__init__()
        self.section_header = None
        self.source = []
        self.target = []