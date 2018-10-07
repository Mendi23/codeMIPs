import itertools

from git import Repo, Commit, Diff
import uritemplate, requests
from urllib.parse import urljoin
from os.path import join as pathjoin
import os

from typing import List, Dict

import DataModule.models as Models
from DataModule.utils import *
from unidiff import PatchedFile, PatchSet

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
    def create(cls, storage, repouri):
        """
        :param repouri: repo uri name.
                        example: "mozilla/DeepSpeech" or KNOWN_SMALL_REPOS[6]
        """
        ret = cls()
        ret.uri = urljoin(BASE_URL, repouri)
        ret.storage =  pathjoin(storage, repouri)
        if os.path.exists(ret.storage):
            print("load existing repo..")
            ret.repo = Repo(ret.storage)
        else:
            print("cloning repo..")
            ret.repo = Repo.clone_from(ret.uri, ret.storage, bare=True)

        print("fetch..")
        ret.repo.remotes.origin.fetch(MASTER)
        print("ready!")
        return ret

    def num_of_commits(self):
        return self.repo.head.commit.count()

    def repo_iterate_commits(self):
        """
        Yo! welcome! this is very important function!

        :return: Commit (Partial or Patch)
        """

        commits: typing.List[Commit] = self.repo.iter_commits(MASTER,
                                                              first_parent=True,
                                                              reverse=True)
        for commit in commits:
            yield commit

            # co = Models.CommitPatch()
            # co.message = commit.message
            # co.committer = commit.committer
            # co.author = commit.author
            # co.sha = commit.hexsha
            # co.date = commit.committed_datetime.strftime("%x %X")
            # # co.stats = commit.stats
            # co.obj = commit
            # # co.patch = self.repo.git.show(commit)
            # yield co



class DataExtractor:
    re_path_file = r"(?:[^/{}\\]+)"
    re_path_part = f"(?:{re_path_file}\/)"
    re_path_full = f"(?:{re_path_part}*{re_path_file})"

    re_patt = f"^(?P<root>{re_path_part}*)" \
              r"(?:\{" \
                f"(?P<before>{re_path_full}) => (?P<after>{re_path_full})" \
                r"\}|" \
                f"(?P<rest>{re_path_file})" \
              f")$"
    re_match = re.compile(re_patt)
    re_normalize = re.compile(r"^[ab]/")

    def __init__(self, savedir, ratio=None):
        self.ratio = ratio if ratio is not None else 0.75
        self.gitdir = Storage.init_save_dir(savedir)
        self.storagedir = Storage.init_save_dir(self.gitdir + "_cache")

    def get_train_test_generator(self, repouri):
        query = Query.create(self.gitdir, repouri)

        return Gen(int(query.num_of_commits() * self.ratio),
                   self._iterate_commits(None, query))

    def _iterate_commits(self, storage: Storage, query: Query):
        for commit in query.repo_iterate_commits():
            cobj = Models.CommitNew()
            cobj.o = commit
            cobj.sha = commit.hexsha
            cobj.message = commit.message
            cobj.date = commit.committed_datetime
            cobj.author = commit.author
            cobj.committer = commit.committer

            patch = PatchSet(query.repo.git.show(commit))
            pf: PatchedFile
            pfiles: Dict[str, PatchedFile] = {}
            for pf in patch:
                source_file = self.re_normalize.sub("/", pf.source_file)
                target_file = self.re_normalize.sub("/", pf.source_file)
                if pf.is_added_file:
                    source_file = target_file
                pfiles[source_file] = pf

            for fname in commit.stats.files.keys():
                groups = self.re_match.match(fname)
                assert groups, f"'{fname}' was not recognized by my regex"
                r = groups["root"]
                if groups["rest"]:
                    source = target = r + groups["rest"]
                    is_renamed = False
                else:
                    source = r + groups["before"]
                    target = r + groups["after"]
                    is_renamed = True
                is_added, is_modified, is_removed = False, True, False
                patch = ""
                if source in pfiles:
                    pf = pfiles[source]
                    is_added, is_modified, is_removed = \
                        pf.is_added_file, pf.is_modified_file, pf.is_removed_file
                    patch = pf.patch_info
                changetype = Models.FileChangesetNew.type_fromtuple(
                    is_added,
                    is_modified,
                    is_removed,
                    is_renamed
                )
                cobj.files.append(Models.FileChangesetNew(
                    source,
                    target,
                    changetype,
                    patch,
                ))

            yield cobj

            # TODO: get commit.stats and parse the file name:
            # TODO: in case of rename filename will be:
            # TODO:         common/root/{origin/path/file.txt => other/file2.txt}
            # TODO: need to parse this

            # TODO: query repo.git.show(commit) and load into PatchSet



if __name__ == "__main__":
    # g = Query()
    # print(g.get_user("urielha"))
    # print(g.repo_num_of_commits("urielha/SimpleObjectAppender"))
    # commit = next(g.repo_iterate_commits("urielha/SimpleObjectAppender"))
    # print(commit)

    de = DataExtractor(STORAGE_PATH)
    for source in [KNOWN_SMALL_REPOS[4],
                   KNOWN_SMALL_REPOS[0],
                   KNOWN_SMALL_REPOS[3],
                   "urielha/SimpleObjectAppender",
                   "urielha/log4stash"]:
        gen = de.get_train_test_generator(source)
        i = itertools.count(1)

        print("train:")
        for commit in gen:
            print(commit.stats.files)
            print(f"1 [{next(i):02}]- {commit.sha}: {commit.date}")

        print("test:")
        for commit in gen:
            print(f"2 [{next(i):02}]- {commit.sha}: {commit.date}")
