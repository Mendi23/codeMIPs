from DataModule.DataQuery import DataExtractor
from pyutils.file_paths import STORAGE_DIR, REPOSITORIES_LIST_FILE

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
        self._super_generators = {}
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

            # Assuming that the caller will finish query the X before stating on Y.
            ## Y is a generator so it will wait after processing the X.
            ## (otherwise - it will provide bugs)
            self.Y = (self._getTest(repo)
                      for repo in repos)

    def _getTrain(self, repo):
        data_extractor = DataExtractor(STORAGE_DIR, repo, ratio=self.ratio)
        ttgen = data_extractor.get_train_test_generator()
        self._super_generators[repo] = ttgen
        return Repo(repo, ttgen)

    def _getTest(self, repo):
        return Repo(repo, list(self._super_generators[repo]))


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
