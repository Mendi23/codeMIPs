import itertools

from git import Repo
import uritemplate, requests
from urllib.parse import urljoin
from os.path import join as pathjoin
import os

import DataModule.models as Models
from DataModule.utils import *

PER_PAGE = 10

ORIGIN = "origin"
MASTER = "master"
STORAGE_PATH = "Storage"
BASE_URL = "https://github.com"

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
        self.repo = None

    @classmethod
    def create(cls, repouri):
        """
        :param repouri: repo uri name.
                        example: "mozilla/DeepSpeech" or KNOWN_SMALL_REPOS[6]
        """
        ret = cls()
        ret.uri = urljoin(BASE_URL, repouri)
        ret.storage =  pathjoin(STORAGE_PATH, repouri)
        if os.path.exists(ret.storage):
            ret.repo = Repo(ret.storage)
        else:
            ret.repo = Repo.clone_from(ret.uri, ret.storage, bare=True)

        ret.repo.remotes.origin.fetch(MASTER)
        return ret

    def num_of_commits(self):
        return self.repo.head.commit.count()

    def repo_iterate_commits(self, maxCommit=None,
                             fetch_diffs_for_commit=True):
        """
        Yo! welcome! this is very important function!

        :param maxCommit: max commit num to reach
        :param fetch_diffs_for_commit: fetch also the files of the commit
        :return: Commit (Partial or Patch)
        """

        commits = reversed(list(self.repo.iter_commits()))
        prev_commit = next(commits)
        for commit in commits:
            co = {}
            co["message"] = commit.message
            co["committer"] = commit.committer
            co["author"] = commit.author
            co["diff"] = prev_commit.diff(commit)
            co["patch"] = self.repo.git.diff(prev_commit, commit)
            yield co
            prev_commit = commit



class DataExtractor:

    def __init__(self, savedir, ratio=None):
        self.ratio = ratio if ratio is not None else 0.75
        self._query = Query()
        self.savedir = Storage.init_save_dir(savedir)

    def get_train_test_generator(self, repouri):
        storage = Storage(self.savedir, repouri)
        if storage.commits_len < 0:
            storage.commits_len = self._query.repo_num_of_commits(repouri)

        return Gen(int(storage.commits_len * self.ratio),
                   self._iter_pages(storage, repouri))

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
    for source in [KNOWN_SMALL_REPOS[4],
                   KNOWN_SMALL_REPOS[0],
                   "urielha/SimpleObjectAppender",
                   "urielha/log4stash"]:
        gen = de.get_train_test_generator(source)
        i = itertools.count(1)
        print("train:")
        for commit in gen:
            print(f"1 [{next(i):02}]- {commit.sha}: {commit.date}")

        print("test:")
        for commit in gen:
            print(f"2 [{next(i):02}]- {commit.sha}: {commit.date}")
