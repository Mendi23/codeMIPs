from DataModule.DataManipulation import create_changes_from_file


class Base:
    def __init__(self):
        self._name = "Base"
        self.id = None
        self.sha = None
        self.url = None
        self.html_url = None

    def __repr__(self):
        return f"{self.__class__}: {self.__dict__.__repr__()}"

    def _hooks(self, json):
        pass

    @classmethod
    def create(cls, json):
        c = cls()
        c.__dict__.update(
            {
                key: val
                for key, val in json.items()
                if key in c.__dict__.keys()
            }
        )
        c._hooks(json)
        return c


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
        self.login = None
        self.repos_url = None
        self.public_repos = None
        self.followers = None
        self.following = None

class CommitPartial(Base):
    """
    CommitPartial is an object which returned from queries like:
     https://api.github.com/repos/urielha/log4stash/commits

    > Doesn't contain `files` <

    {
        commit: {
            comitter: {name, email, date},
            tree (Base), message,
        },
        comitter: { login, type },
    }
    """

    def __init__(self):
        super().__init__()
        self.committer = None
        self.message = None
        self.date = None
        self.tree = None

    def _hooks(self, json):
        self.committer = User.create(json["committer"])

        assert json["commit"] is not None
        commit = json["commit"]
        self.tree = Base.create(commit["tree"])
        self.message = commit["message"]
        self.date = commit["committer"]["date"]



class Commit(CommitPartial):
    """
    Commit is a CommitPartial but with `files`
    """
    def __init__(self):
        super().__init__()
        self.files = None

    def _hooks(self, json):
        super()._hooks(json)
        self.files = [FileChangeset.create(f) for f in json["files"]]

    def iterate_changes(self):
        for file in self.files:
            yield from create_changes_from_file(file)

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


class Change:
    def __init__(self):
        self.segment = None
        self.type = None
