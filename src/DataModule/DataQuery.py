import itertools

from agithub.GitHub import GitHub
import uritemplate, requests
from bs4 import BeautifulSoup

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
    """
    This is your dragon handle to the mighty github!!!!
    Oh poor user, you are about to see the full power of github on your tiny
    programmer's hands.
    """

    def __init__(self):
        self._g = GitHub()

    def _get_last_page(self, partial_req):
        has_next = lambda headers: any(
            h for h in headers if "Link" in h and "next" in h[1])

        for pageNum in itertools.count(1):
            res = partial_req.get(page=pageNum)
            headers = self._g.getheaders()
            assert res[0] == 200
            if not has_next(headers):
                return pageNum


    def get_user(self, useruri):
        """
        :param useruri: user *login* name. example: "mozilla"
        :return: User object (see models.py)
        """
        res = self._g.users[useruri].get()
        assert res[0] == 200
        return Models.User.create(res[1])

    def user_repos(self, useruri):
        """
        :param useruri: user *login* name. example: "mozilla"
        :return: list of Repo objects (see models.py)
        """
        repos = self._g.users[useruri].repos.get()
        assert repos[0] == 200
        return [
            Models.Repo.create(repo)
            for repo in repos[1]
        ]

    def repo_num_of_commits(self, repouri):
        """
        :param useruri: repo uri name.
                        example: "mozilla/DeepSpeech" or KNOWN_SMALL_REPOS[6]
        :return: number
        """

        # 1. get the repo api:
        res = self._g.repos[repouri].get()
        assert res[0] == 200
        repo = Models.Repo.create(res[1])

        # 2. fetch full html page
        req = requests.get(repo.html_url)
        assert req.status_code == 200

        # 3. parse the page and return commits num:
        soup = BeautifulSoup(req.content, 'html.parser')
        commits = soup.find('li', 'commits').find('span', 'num').get_text().strip()
        return int(commits)

    def repo_iterate_commits(self, repouri, fetch_files_for_commit=True):
        """
        Yo! welcome! this is very important function!
        
        :param repouri: repo uri name.
                        example: "mozilla/DeepSpeech" or KNOWN_SMALL_REPOS[6]
        :param fetch_files_for_commit: fetch also the files of the commit
        :return: Commit
        """
        lastPage = self._get_last_page(self._g.repos[repouri].commits)

        for pageNum in range(lastPage, 0, -1):
            res = self._g.repos[repouri].commits.get(page=pageNum)
            assert res[0] == 200

            for commit in reversed([Models.CommitPartial.create(c) for c in res[1]]):
                if fetch_files_for_commit:
                    real_commit = self._g.repos[repouri].commits[commit.sha].get()
                    assert real_commit[0] == 200
                    yield Models.Commit.create(real_commit[1])
                else:
                    yield commit

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
