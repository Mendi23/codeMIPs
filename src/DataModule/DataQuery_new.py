import datetime
import itertools
from pprint import pprint

from git import Repo, Commit, Diff
import uritemplate, requests
from urllib.parse import urljoin
from os.path import join as pathjoin
import os

from typing import List, Dict

import DataModule.models_new as MM
from DataModule.utils import *
from unidiff import PatchedFile, PatchSet

PER_PAGE = 100

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
        ret.storage = pathjoin(storage, repouri)
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
        yield from commits


class _CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, MM.Base):
            return o.serialize()
        return json.JSONEncoder.default(self, o)


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

    def __init__(self, savedir, ratio=None):
        self.ratio = ratio if ratio is not None else 0.75
        self.gitdir = Storage.init_save_dir(savedir)
        self.storagedir = Storage.init_save_dir(self.gitdir + "_cache")

    def get_train_test_generator(self, repouri):
        query = Query.create(self.gitdir, repouri)

        return Gen(int(query.num_of_commits() * self.ratio),
                   self._iterate_commits(query))

    def _iterate_commits(self, query: Query):
        jsons_filename = pathjoin(self.storagedir, "data.{:03}.jsons")
        fo = open(jsons_filename.format(0), "w")
        for i, commit in enumerate(query.repo_iterate_commits()):
            cobj = self._create_commit(commit)

            # ~~~~~~~~~ save patches mapping ~~~~~~~~~~~~~~~~
            patch_by_files = PatchSet(query.repo.git.show(commit))
            pfiles: Dict[str, PatchedFile] = {
                pf.path: pf for pf in patch_by_files
            }
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            # ~~~~~~~~~ convert the stats ~~~~~~~~~~~~~~~~
            for fname in commit.stats.files.keys():
                changetype, source, target = self._extract_metadata(fname)

                # -> fetch the patches and convert
                patches = []
                if source in pfiles:
                    pf = pfiles[source]
                    self._fill_patches(patches, pf)
                    if changetype != MM.ChangeEnum.RENAMED:
                        changetype = MM.ChangeEnum_fromtuple(
                            pf.is_added_file,
                            pf.is_modified_file,
                            pf.is_removed_file,
                            False
                        )
                # ---

                # -> creating file changeset
                fc = MM.FileChangeset()
                fc.changetype = changetype
                fc.source = source
                fc.target = target
                fc.patches = patches
                cobj.files.append(fc)
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            cobj.files.sort() # place "RENAME" before others

            Storage.export_object_to_file(cobj, fo, _CustomJsonEncoder)
            if i > 0 and i % PER_PAGE == 0:
                fo.close()
                fo = open(jsons_filename.format(int(i / PER_PAGE)), "w")
            yield cobj
        ### END

        fo.close()

    def _extract_metadata(self, fname):
        changetype = MM.ChangeEnum.MODIFIED
        groups = self.re_match.match(fname)
        assert groups, f"'{fname}' was not recognized by my regex"

        r = groups["root"]
        if groups["rest"]:
            source = target = r + groups["rest"]
        else:
            source = r + groups["before"]
            target = r + groups["after"]
            changetype = MM.ChangeEnum.RENAMED
        return changetype, source, target

    def _fill_patches(self, patches, pf):
        for inner in pf:
            patch = MM.Patch()
            patch.source_lines = inner.source
            patch.target_lines = inner.target
            patch.section_header = inner.section_header
            patches.append(patch)

    def _create_commit(self, commit) -> MM.Commit:
        cobj = MM.Commit()
        cobj.sha = commit.hexsha
        cobj.message = commit.message
        cobj.date_timestamp = commit.committed_datetime.timestamp()
        cobj.author = MM.User()
        cobj.committer = MM.User()

        cobj.author.name = commit.author.name
        cobj.author.email = commit.author.email
        cobj.committer.name = commit.committer.name
        cobj.committer.email = commit.committer.email
        return cobj


if __name__ == "__main__":
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
            d = datetime.datetime.fromtimestamp(commit.date_timestamp).strftime('%X-%x')
            print(f"1 [{next(i):02}]- {commit.sha}: {d}")

        print("test:")
        for commit in gen:
            print(f"2 [{next(i):02}]- {commit.sha}: {commit.date_timestamp}")
