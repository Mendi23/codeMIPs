import itertools

from agithub.GitHub import GitHub
import uritemplate, requests

import DataModule.models as Models
from DataModule.utils import *

PER_PAGE = 10

BASE_URL = "https://api.github.com"
KNOWN_SMALL_REPOS = [
    "Microsoft/DirectXShaderCompiler",
    "fragglet/c-algorithms",
    "TheAlgorithms/C-Plus-Plus",
    "TheAlgorithms/C",
    "nlohmann/json",
    "stedolan/jq",
    "mozilla/DeepSpeech",
    "Alexpux/mingw-w64",
]
KNOWN_BIG_REPOS = [
    "torvalds/linux",
    "videolan/vlc",
    "tensorflow/tensorflow",
    "nginx/nginx",
    "electron/electron",
    "bitcoin/bitcoin",
    "google/protobuf",
    "mozilla/rr",
    "mozilla/gecko-dev",
    "Microsoft/ELL",
]


class Query:
    """
    This is your dragon handle to the mighty github!!!!
    Oh poor user, you are about to see the full power of github on your tiny
    programmer's hands.
    """

    def __init__(self):
        self._g = GitHub()

    def _get_last_page(self):
        headers = self._g.getheaders()
        link = next(h for h in headers if "Link" in h)
        match = re.search(r'[&?]page=(\d+)[^;]+;\s*rel="last"', link[1])
        return int(match.group(1))

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
        self._g.repos[repouri].commits.get(per_page=1)
        lastPage = self._get_last_page()
        return lastPage

    def repo_iterate_commits(self, repouri, maxPage=None,
                             fetch_files_for_commit=True, withPageNum=False):
        """
        Yo! welcome! this is very important function!
        
        :param repouri: repo uri name.
                        example: "mozilla/DeepSpeech" or KNOWN_SMALL_REPOS[6]
        :param maxPage: max page to reach (actually form this page we will start)
        :param fetch_files_for_commit: fetch also the files of the commit
        :param withPageNum: yield also page number
        :return: Commit
        """

        if maxPage is not None:
            lastPage = maxPage
        else:
            self._g.repos[repouri].commits.get(per_page=PER_PAGE)
            lastPage = self._get_last_page()

        for pageNum in range(lastPage, 0, -1):
            res = self._g.repos[repouri].commits.get(per_page=PER_PAGE, page=pageNum)
            assert res[0] == 200

            for commit in reversed([Models.CommitPartial.create(c) for c in res[1]]):
                if fetch_files_for_commit:
                    real_commit = self._g.repos[repouri].commits[commit.sha].get()
                    assert real_commit[0] == 200
                    toYield = Models.Commit.create(real_commit[1])
                else:
                    toYield = commit

                if withPageNum:
                    yield pageNum, toYield
                else:
                    yield toYield

    def search_repo(self, text, language):
        pass

    def search_user(self, user):
        self._g.users[user].get()


class DataExtractor:

    def __init__(self, savedir, ratio=None):
        self.ratio = ratio if ratio is not None else 0.75
        self._query = Query()
        self.savedir = Storage.init_save_dir(savedir)

    def get_train_test_generator(self, repouri):
        storage = Storage(self.savedir, repouri)
        if storage.commits_len < 0:
            storage.commits_len = self._query.repo_num_of_commits(repouri)

        generator = iter(self._iter_pages(storage, repouri))
        return Gen(int(storage.commits_len * self.ratio),
                   generator)

    def _iter_pages(self, storage: Storage, repouri):
        pages = storage.get_pages()
        pages_sorted = sorted(pages.keys(), reverse=True)
        for i in pages_sorted:
            for commit in pages[i]:
                yield commit

        maxPage = None if len(pages) == 0 else min(pages.keys()) - 1
        repo_iter = self._query.repo_iterate_commits(repouri,
                                                     maxPage=maxPage,
                                                     withPageNum=True)
        commits = []
        lastpage = None
        for page, commit in repo_iter:
            if lastpage is not None and lastpage != page:
                storage.add_page(lastpage, commits)
                commits = []
            lastpage = page
            commits.append(commit)
            yield commit

        if lastpage is not None and any(commits):
            storage.add_page(lastpage, commits)

        storage.dispose()


if __name__ == "__main__":
    # g = Query()
    # print(g.get_user("urielha"))
    # print(g.repo_num_of_commits("urielha/SimpleObjectAppender"))
    # commit = next(g.repo_iterate_commits("urielha/SimpleObjectAppender"))
    # print(commit)

    de = DataExtractor("Storage")
    # gen = de.get_train_test_generator(KNOWN_SMALL_REPOS[0])
    gen = de.get_train_test_generator("urielha/heapdict")
    i = itertools.count(1)
    print("train:")
    for commit in gen:
        print(f"1 [{next(i):02}]- {commit.sha}: {commit.message} | {commit.date}")

    print("test:")
    for commit in gen:
        print(f"2 [{next(i):02}]- {commit.sha}: {commit.message} | {commit.date}")
