
class Base:
    def __init__(self):
        self._name = "Base"
        self.id = None
        self.sha = None
        self.url = None
        self.html_url = None

    def __repr__(self):
        return f"{self.__class__}: {self.__dict__.__repr__()}"

    def hooks(self):
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
        c.hooks()
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
    def __init__(self):
        super().__init__()
        self.commit = None
        self.committer = None

    def hooks(self):
        if self.committer is not None:
            self.committer = User.create(self.committer)
        if self.commit is not None:
            self.commit = CommitPartial.create(self.commit)

class Commit(CommitPartial):
    def __init__(self):
        super().__init__()
        self.files = None

    def hooks(self):
        if self.files is not None and len(self.files) > 0:
            self.files = [File.create(f) for f in self.files]

class File(Base):
    def __init__(self):
        super().__init__()
        self.filename = None
        self.status = None
        self.additions = None
        self.deletions = None
        self.changes = None
        self.patch = None
        self.contents_url = None
        self.raw_url = None
