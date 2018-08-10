import itertools

from agithub.GitHub import GitHub
import uritemplate, requests

import DataModule.models as Models

BASE_URL = "https://api.github.com"
KNOWN_SMALL_REPOS = [
    "/Microsoft/DirectXShaderCompiler ",
    "/fragglet/c-algorithms",
    "/TheAlgorithms/C-Plus-Plus",
    "/TheAlgorithms/C",
    "/nlohmann/json",
    "/stedolan/jq",
    "/mozilla/DeepSpeech",
    "/Alexpux/mingw-w64",
]
KNOWN_BIG_REPOS = [
    "/torvalds/linux",
    "/videolan/vlc",
    "/tensorflow/tensorflow",
    "/nginx/nginx",
    "/electron/electron",
    "/bitcoin/bitcoin",
    "/google/protobuf",
    "/mozilla/rr",
    "/mozilla/gecko-dev",
    "/Microsoft/ELL",
]

class Query:

    def __init__(self):
        self._g = GitHub()

    def get_user(self, useruri):
        res = self._g.users[useruri].get()
        assert res[0] == 200
        return Models.User.create(res[1])

    def user_repos(self, useruri):
        repos = self._g.users[useruri].repos.get()
        assert repos[0] == 200
        return [
            Models.Repo.create(repo)
            for repo in repos[1]
        ]

    def repo_num_of_commits(self, repouri):
        return len(list(self.repo_iterate_commits(repouri, False)))

        # TODO: exract commit using HTMLParser - is much faster
        res = self._g.repos[repouri].get()
        assert res[0] == 200
        repo = Models.Repo.create(res[1])
        requests.get(repo.html_url) # get full html page
        # TODO: continue...


    def repo_iterate_commits(self, repouri, fetch_real_commit=True):
        has_next = lambda headers: len([h for h in headers if "Link" in h and "next" in h[1]]) > 0

        for pageNum in itertools.count(1):
            res = self._g.repos[repouri].commits.get(page=pageNum)
            headers = self._g.getheaders()
            assert res[0] == 200

            for commit in (Models.CommitPartial.create(c) for c in res[1]):
                if fetch_real_commit:
                    real_commit = self._g.repos[repouri].commits[commit.sha].get()
                    assert real_commit[0] == 200
                    yield Models.Commit.create(real_commit[1])
                else:
                    yield commit

            if not has_next(headers):
                break


    def search_repo(self, text, language):
        pass

    def search_user(self, user):
        self._g.users[user].get()


if __name__ == '__main__':
    g = Query()
    print(g.get_user("urielha"))
    print(g.repo_num_of_commits("urielha/log4stash"))
    commit = next(g.repo_iterate_commits("urielha/log4stash"))
    print(commit)
