import base64
import gzip


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
        return self.__dict__


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
            committer: {name, email, date},
            tree (Base), message,
        },
        committer: { login, type },
    }
    """

    def __init__(self):
        super().__init__()
        self.committer = User()
        self.message = None
        self.date = None
        # self.tree = Base()

    def _hooks(self, json, objectLoaded):

        if not objectLoaded:
            assert json["commit"] is not None
            commit = json["commit"]
            # self.tree = Base.create(commit["tree"], objectLoaded)
            self.message = commit["message"]
            self.date = commit["committer"]["date"]
        else:
            commit = json

        try:
            self.committer = User.create(commit["committer"], objectLoaded)
        except:
            print(json)
            raise



class Commit(CommitPartial):
    """
    Commit is a CommitPartial but with `files`
    """
    def __init__(self):
        super().__init__()
        self.files = None

    def _hooks(self, json, objectLoaded):
        super()._hooks(json, objectLoaded)
        self.files = [FileChangeset.create(f, objectLoaded) for f in json["files"]]

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
            self.patch = gzip.decompress(base64.b64decode(self.patch.encode())).decode()

    def serialize(self):
        json = super().serialize()
        json["patch"] = base64.b64encode(gzip.compress(self.patch.encode())).decode()
        return json