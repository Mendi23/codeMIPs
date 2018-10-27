from collections import defaultdict

from CSR import CsrFiles
from DataModule.DataQuery import DataExtractor
from pyutils.file_paths import STORAGE_DIR, REPOSITORIES_LIST_FILE


class Provider:
    def __init__(self, k_commits):
        gen = (line.strip().split("#", 1)[0]
                    for line in open(REPOSITORIES_LIST_FILE))
        self.repos = [repo for repo in gen if repo]
        print("Repositories:")
        for repo in self.repos:
            print(f" - {repo}")

        self.k_commits = k_commits
        self._super_generators = {}

        self.X = [self._getTrain(repo)
                  for repo in self.repos]
        self.Y = (self._getTest(repo)
                  for repo in self.repos)

    def _getTrain(self, repo):
        code_graph = CsrFiles()
        data_extractor = DataExtractor(STORAGE_DIR, repo, k_commits=self.k_commits)
        ttgen = data_extractor.get_train_test_generator()
        self._super_generators[repo] = ttgen
        return (
            code_graph.apply_changes_from_commit(commit)
            for commit in ttgen
        )

    def _getTest(self, repo):
        ttgen = self._super_generators[repo]
        users = defaultdict(set)
        for commit in ttgen:
            users[commit.author].update(file.source for file in commit.files)

        return users



if __name__ == '__main__':
    p = Provider(1)
    for commits in p.X:
        print("repo...")
        for commit in commits:
            print("  commit...")
            for action in commit:
                print("    " + str(action))

    for users in p.Y:
        print("repo...")
        for user, files  in users.items():
            print("  " + str(user))
            print("     " + str(files))