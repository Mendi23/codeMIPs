import functools
import itertools
# import uritemplate, requests
from functools import partial
from os.path import join as pathjoin
from typing import Dict, Iterator
from urllib.parse import urljoin

from git import Repo, Commit
from unidiff import PatchedFile, PatchSet

from DataModule.utils import *

from pyutils.file_paths import STORAGE_DIR

CACHE_THE_DATA_MF = True
DEBUG_1 = False

PER_PAGE = 100

ORIGIN = "origin"
MASTER = "master"
BASE_URL = "https://github.com"

KNOWN_SMALL_REPOS = [
    "urielha/SimpleObjectAppender",
    "urielha/log4stash",
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


class GithubQuery:
    """
    This is your dragon handle to the mighty github!!!!
    Oh poor user, you are about to see the full power of github on your tiny
    programmer's hands.
    """

    def __init__(self):
        self.repo = None
        self.uri = None
        self.storage = None

    @classmethod
    def create(cls, storage, repouri):
        """
        Create instance of GithubQuery.
        Cloning the repository to local storage if needed.
        Fetch last version of the repository.
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
        return self.repo.branches.master.commit.count(first_parent=True)

    def repo_iterate_commits(self) -> Iterator[Commit]:
        """
        Iterate over commits in "master" from the first (oldest) commit
        to the last.
        Excluding forks to other branches.
        """
        return self.repo.iter_commits(MASTER,
            first_parent=True,
            reverse=True)


class DataExtractor:
    re_path_file = r"(?:[^/{}\\=>]+)"
    re_path_part = f"(?:{re_path_file}\/)"
    re_path_full = f"(?:{re_path_part}*{re_path_file})"

    re_patt = "^(?:" \
              f"(?P<root>{re_path_part}*)" \
              r"(?:\{" \
              f"(?P<before>{re_path_full})? => (?P<after>{re_path_full})?" \
              r"\})" \
              f"\/?(?P<rest>{re_path_full})?" \
              "|" \
              f"(?P<before2>{re_path_full})? => (?P<after2>{re_path_full})?" \
              "|" \
              f"(?P<rest2>{re_path_full})" \
              ")$"
    re_match = re.compile(re_patt)

    def __init__(self, savedir, ratio=None):
        self.ratio = ratio if ratio is not None else 0.75
        self.gitdir = Storage.init_save_dir(savedir)
        self.storagedir = Storage.init_save_dir(self.gitdir + "_cache")

    def get_train_test_generator(self, repouri):
        self.query = query = GithubQuery.create(self.gitdir, repouri)
        jsons_filename = pathjoin(self.storagedir,
                                  Storage.get_valid_filename(repouri))
        jsons_export = functools.partial(Storage.export_object_to_json_file,
                                         encoder=CustomJsonEncoder)
        jsons_import = functools.partial(Storage.import_objects_from_json_file,
                                         decoder=Models.Commit.create,
                                         decode_stacked=decode_json_stacked)
        # noinspection PyTypeChecker
        self.storage = Storage(jsons_filename, PER_PAGE, jsons_export, jsons_import)

        return Gen(int(query.num_of_commits() * self.ratio),
            self._iterate_commits(query)
        )

    def load_commits(self):
        return self.storage.load_all()

    def _iterate_commits(self, query: GithubQuery):
        if CACHE_THE_DATA_MF:
            yield from self.load_commits()
        skip_n = self.storage.objects_count

        for i, commit in enumerate(query.repo_iterate_commits()):
            if i < skip_n: continue

            cobj = self._create_commit(commit)

            # ~~~~~~~~~ save patches mapping ~~~~~~~~~~~~~~~~
            # `git show` doesn't show merges details so here we had to
            # give it a 2-commits diff to show (unless it is the first commit)
            show_str = f"{commit.parents[0]}..{commit}" if commit.parents else commit
            patch_by_files = PatchSet(query.repo.git.show(show_str))
            pfiles: Dict[str, PatchedFile] = {
                pf.path: pf for pf in patch_by_files
            }
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            # ~~~~~~~~~ convert the stats ~~~~~~~~~~~~~~~~
            for fname in commit.stats.files.keys():
                fc = self._create_file_changeset(fname, pfiles, commit.hexsha)
                cobj.files.append(fc)
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            cobj.files.sort()  # place "RENAME" before others

            if CACHE_THE_DATA_MF:
                self.storage.save_obj(cobj)
            yield cobj
        ### END

        self.storage.dispose()

    def _create_commit(self, commit) -> Models.Commit:
        cobj = Models.Commit()
        cobj.sha = commit.hexsha
        cobj.message = commit.message
        cobj.date_timestamp = commit.committed_datetime.timestamp()
        cobj.author = Models.User()
        cobj.committer = Models.User()

        cobj.author.name = commit.author.name
        cobj.author.email = commit.author.email
        cobj.committer.name = commit.committer.name
        cobj.committer.email = commit.committer.email
        return cobj

    def _create_file_changeset(self, fname, pfiles, commit_sha):
        changetype, source, target = self._extract_metadata(fname)

        # -> fetch the patches and convert
        patches = []
        if source in pfiles:
            self._fill_patches(patches, pfiles[source])
            if changetype != Models.ChangeEnum.RENAMED:
                changetype = Models.ChangeEnum_fromdescriptor(pfiles[source])

        if DEBUG_1 and len(patches) == 0 and changetype != Models.ChangeEnum.RENAMED:
            print(f"{commit_sha}: filename: {fname}, got none patches.")
        # ---

        # -> creating file changeset
        fc = Models.FileChangeset()
        fc.changetype = changetype
        fc.source = source
        fc.target = target
        fc.patches = patches
        return fc

    def _extract_metadata(self, fname):
        changetype = Models.ChangeEnum.MODIFIED
        groups = self.re_match.match(fname)
        assert groups, f"'{fname}' was not recognized by my regex"

        if groups["rest2"]:
            source = target = groups["rest2"]
        elif groups["before2"] or groups["after2"]:
            source = groups["before2"] or ""
            target = groups["after2"] or ""
        else:
            root = groups["root"] or ""
            rest = groups["rest"] or ""
            source = root + (groups["before"] or "") + rest
            target = root + (groups["after"] or "") + rest

        if source != target:
            changetype = Models.ChangeEnum.RENAMED
        return changetype, source, target

    def _fill_patches(self, patches, pf):
        for inner in pf:
            patch = Models.Patch()
            patch.source_lines = inner.source
            patch.target_lines = inner.target
            patch.section_header = inner.section_header
            patches.append(patch)


if __name__ == "__main__":
    de = DataExtractor(STORAGE_DIR)
    for source in KNOWN_SMALL_REPOS[:2]:
        gen = de.get_train_test_generator(source)
        i = itertools.count(1)

        print(de.query.num_of_commits())
        print("train: " + str(len(list(gen))))
        # for i, commit in gen:
        #     print(f"{i:03}: {commit.hexsha}")
        #     print(f"1 [{next(i):02}]- {commit.sha}: {commit.date_str}")

        print("test: " + str(len(list(gen))))
        # for i, commit in gen:
        #     print(f"{i:03}: {commit.hexsha}")
        #     print(f"2 [{next(i):02}]- {commit.sha}: {commit.date_str}")

        if CACHE_THE_DATA_MF:
            print("load:")
            commits = list(de.load_commits())
            print(len(commits))
            print(commits[0])
