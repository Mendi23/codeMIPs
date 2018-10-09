import base64
import gzip

import typing
from enum import Enum


def _encode_string(s: str) -> str:
    compressed = gzip.compress(str(s).encode())
    return base64.b64encode(compressed).decode()

def _decode_string(s: str) -> str:
    decoded = base64.b64decode(str(s).encode())
    return gzip.decompress(decoded).decode()

class Base:
    def __init__(self):
        self._name = self.__class__.__name__
        self.id = None
        self.sha = None
        self.url = None
        self.html_url = None

    def __repr__(self):
        return f"<{self._name}: {self.__dict__.__repr__()}>"

    def _hooks(self, json, objectLoaded):
        pass

    @classmethod
    def create(cls, json, objectLoaded=False):
        c = cls()
        c.__dict__.update(
            {
                key: val
                for key, val in json.items()
                if key in c.__dict__.keys()
            }
        )
        c._hooks(json, objectLoaded)
        return c

    def serialize(self):
        return {k:v for k,v in self.__dict__.items() if v is not None}


class Repo(Base):
    def __init__(self):
        super().__init__()
        self.contributors_url = None
        self.commits_url = None
        self.name = None
        self.full_name = None
        self.size = None
        self.language = None


class User(Base):
    def __init__(self):
        super().__init__()
        self.name = None
        self.email = None
        # self.login = None
        # self.public_repos = None
        # self.followers = None
        # self.following = None

class CommitPartial(Base):
    """
    CommitPartial is an object which returned from queries like:
     https://api.github.com/repos/urielha/log4stash/commits

    > Doesn't contain `files` <

    {
        commit: {
            author: {name, email, date},
            committer: {name, email, date},
            tree (Base), message,
        },
        author: { login, type },
        committer: { login, type },
    }
    """

    def __init__(self):
        super().__init__()
        self.author = User()
        self.committer = User()
        self.message = None
        self.date = None
        # self.tree = Base()

    def _hooks(self, json, objectLoaded):

        if not objectLoaded:
            assert "commit" in json and json["commit"] is not None
            commit = json["commit"]
            # self.tree = Base.create(commit["tree"], objectLoaded)
            self.message = commit["message"]
            self.date = commit["committer"]["date"]
        else:
            commit = json

        try:
            self.committer = User.create(commit["committer"], objectLoaded)
            self.author = User.create(commit["author"], objectLoaded)
        except:
            print(json)
            raise



class CommitFiles(CommitPartial):
    """
    CommitFiles is a CommitPartial but with `files`
    """
    def __init__(self):
        super().__init__()
        self.files: typing.List[FileChangeset] = None

    def _hooks(self, json, objectLoaded):
        super()._hooks(json, objectLoaded)
        if "files" in json and json["files"] is not None:
            self.files = [FileChangeset.create(f, objectLoaded) for f in json["files"]]


class CommitPatch(CommitPartial):
    """
    CommitPatch is a CommitPartial but with `patch` that contain files data
    """
    def __init__(self, commitPartial: CommitPartial = None, patch = None):
        super().__init__()
        if commitPartial is not None:
            self.__dict__ = commitPartial.__dict__
        self.patch: str = patch
        self.stats = None

    def _hooks(self, json, objectLoaded):
        if objectLoaded and "patch" in json and json["patch"] is not None:
            self.patch = _decode_string(self.patch)

    def serialize(self):
        json = super().serialize()
        json["patch"] = _encode_string(self.patch)
        return json


class FileChangeset(Base):
    def __init__(self):
        super().__init__()
        self.filename = None
        self.status = None # renamed / modified / added / deleted
        self.additions = None
        self.deletions = None
        self.changes = None
        self.patch = None
        self.contents_url = None
        self.raw_url = None
        self.previous_filename = None

    def _hooks(self, json, objectLoaded):
        if objectLoaded:
            self.patch = _decode_string(self.patch)

    def serialize(self):
        json = super().serialize()
        json["patch"] = _encode_string(self.patch)
        return json
