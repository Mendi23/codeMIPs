from collections import deque
from typing import Generic, Iterable

from DataModule.DataQuery import DataExtractor, TypeVar
from pyutils.file_paths import STORAGE_DIR, REPOSITORIES_LIST_FILE

T = TypeVar('T')


class ReusableGenerator(Generic[T]):
    def __init__(self, gen: Iterable[T]):
        self._gen = iter(gen)
        self._arr = deque()

    def __iter__(self):
        if self._arr:
            self._gen = None
            return iter(self._arr)
        return self

    def __next__(self) -> T:
        res = next(self._gen)
        self._arr.append(res)
        return res


class Repo:
    def __init__(self, name, gen):
        self.gen = gen
        self.name = name

    def __iter__(self):
        return iter(self.gen)


class Provider:
    def __init__(self, ratio, repo=None):
        """
        IMPORTANT: Assuming the caller will consume the X before consuming Y.
        """
        self.ratio = ratio
        self.data_extractors = {}
        if repo is not None:
            self.X = self._getTrain(repo)
            self.Y = self._getTest(repo)
        else:
            gen = (line.strip().split("#", 1)[0]
                   for line in open(REPOSITORIES_LIST_FILE))
            repos = [repo for repo in gen if repo]
            print("Repositories:")
            for repo in repos:
                print(f" - {repo}")
            # This is important:
            ## the X list is not generator so all the preperations before run would be ready
            ## avoiding surprises (not all, but some) in the middle of the process.
            self.X = [self._getTrain(repo)
                      for repo in repos]

            self.Y = [self._getTest(repo)
                      for repo in repos]

    def _getTrain(self, repo):
        data_extractor = DataExtractor(STORAGE_DIR, repo, ratio=self.ratio)
        self.data_extractors[repo] = data_extractor
        return Repo(repo, data_extractor.get_train())

    def _getTest(self, repo):
        data_extractor = self.data_extractors[repo]
        return Repo(repo, ReusableGenerator(data_extractor.get_test()))

    @staticmethod
    def removeRepo(repo):
        data = open(REPOSITORIES_LIST_FILE).read()
        i = data.index(repo)
        if "#" not in data[i - 3:i]:
            open(REPOSITORIES_LIST_FILE, "w").write(
                data[:i] + "# TOO MUCH FILES # " + data[i:])


if __name__ == '__main__':
    p = Provider(0.8)
    for repo in p.X:
        print(f"processing repo {repo.name}")
        for commit in repo:
            print((commit.sha, commit.message))

    for repo in p.Y:
        print(f"processing repo {repo.name}")
        for commit in repo:
            print((commit.sha, commit.message))
