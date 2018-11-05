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

CACHE_THE_DATA = True
DEBUG_1 = False

PER_PAGE = 100

ORIGIN = "origin"
MASTER = "master"
BASE_URL = "https://github.com"


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
            print(f"[DataQuery] - load existing repo: {repouri}..")
            ret.repo = Repo(ret.storage)
        else:
            print(f"[DataQuery] - cloning repo: {repouri}..")
            ret.repo = Repo.clone_from(ret.uri, ret.storage, bare=True)

        print("[DataQuery] - ready!")
        return ret

    def num_of_commits(self):
        return self.repo.branches.master.commit.count(first_parent=True)

    def repo_iterate_commits(self, until=None, start_from=None) -> Iterator[Commit]:
        """
        Iterate over commits in "master" from the first (oldest) commit
        to the last.
        Excluding forks to other branches.
        :param until - index from the END (i.e. until=1 is until 1 before the end)
        :param start_from - index from the END
        """
        assert until is None or start_from is None, "can't have both `until` and `start_from` set with value"

        branch = MASTER
        if until is not None:
            branch = f"{MASTER}~{until}"
        elif start_from is not None:
            branch = f"{MASTER}~{start_from}..{MASTER}"

        return self.repo.iter_commits(branch,
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
              f"(?P<rest>\/?{re_path_full})?" \
              "|" \
              f"(?P<before2>{re_path_full})? => (?P<after2>{re_path_full})?" \
              "|" \
              f"(?P<rest_only>{re_path_full})" \
              ")$"
    re_match = re.compile(re_patt)

    def __init__(self, savedir, repouri, ratio=None, k_commits=None):
        self.ratio = ratio if ratio is not None else 0.75
        self.k_commits = k_commits if k_commits is not None else -1
        self.gitdir = Storage.init_save_dir(savedir)
        self.storagedir = Storage.init_save_dir(self.gitdir + "_cache")
        self.repouri = repouri

        self.query = GithubQuery.create(self.gitdir, self.repouri)

        self.num_of_commits = self.query.num_of_commits()
        self.first_slice = int(self.num_of_commits * self.ratio)
        if self.k_commits > 0:
            assert self.num_of_commits > self.k_commits, \
                f"Asked to slice {self.k_commits} commits but got only total of {self.num_of_commits} commits."
            self.first_slice = self.num_of_commits - self.k_commits

        print(f"[DataQuery] - Repo: {repouri}, commits: {self.num_of_commits}, train slice: {self.first_slice}")

    def initialize_repo_storage(self, suffix=''):
        jsons_filename = pathjoin(self.storagedir,
                                  Storage.get_valid_filename(self.repouri + suffix))

        jsons_export = Storage.export_object_to_json_file
        jsons_import = functools.partial(Storage.import_objects_from_json_file,
                                         decoder=Models.Commit.create)
        # noinspection PyTypeChecker
        storage = Storage(jsons_filename, PER_PAGE, jsons_export, jsons_import)
        return storage

    def get_train(self) -> Iterable[Models.Commit]:
        storage = self.initialize_repo_storage()
        until = self.num_of_commits - self.first_slice
        return self._iterate_commits(storage, until=until)

    def get_test(self) -> Iterable[Models.Commit]:
        storage = self.initialize_repo_storage("_test")
        start_from = self.num_of_commits - self.first_slice
        return self._iterate_commits(storage, start_from=start_from)

    def load_commits(self, storage: Storage):
        return storage.load_all()

    def _iterate_commits(self, storage: Storage, until=None, start_from=None):
        query: GithubQuery = self.query

        if CACHE_THE_DATA:
            firsttime = True
            for commit in self.load_commits(storage):
                if firsttime:
                    print("SOME OF THE DATA IS LOADED FROM CACHE!")
                    firsttime = False
                yield commit
        skip_n = storage.objects_count

        for i, commit in enumerate(query.repo_iterate_commits(until, start_from)):
            if i < skip_n: continue

            cobj = self._create_commit(commit)

            # ~~~~~~~~~ save patches mapping ~~~~~~~~~~~~~~~~
            # `git show` doesn't show merges details so here we had to
            # give it a 2-commits diff to show (unless it is the first commit)
            show_str = f"{commit.parents[0]}..{commit}" if commit.parents else commit
            patch_by_files = PatchSet(query.repo.git.show(show_str, first_parent=True))
            pfiles: Dict[str, PatchedFile] = {
                pf.path: pf for pf in patch_by_files
            }
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            # ~~~~~~~~~ convert the stats ~~~~~~~~~~~~~~~~
            for fname in commit.stats.files.keys():
                fc = self._create_file_changeset(fname, pfiles, commit.hexsha)
                cobj.files.append(fc)
            cobj.files.sort()  # place "RENAME" before others
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            if CACHE_THE_DATA:
                storage.save_obj(cobj)
            yield cobj
        ### END

        storage.dispose()

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
        chunk = fname
        a, b = chunk.find("{"), chunk.find("}")
        a = a if a >= 0 else 0
        b = b if b >= 0 else len(chunk)

        root, chunk, rest = chunk[:a], chunk[a:b], chunk[b:]
        if " => " in chunk:
            before, after = chunk.split(" => ", 1)
        else:
            before = after = chunk

        source = self._build_path((root, before, rest))
        target = self._build_path((root, after, rest))

        if source != target:
            changetype = Models.ChangeEnum.RENAMED
        return changetype, source, target

    def _extract_metadata__old(self, fname):
        changetype = Models.ChangeEnum.MODIFIED
        groups = self.re_match.match(fname)
        assert groups, f"'{fname}' was not recognized by my regex"

        if groups["rest_only"]:
            source = target = groups["rest_only"]
        elif groups["before2"] or groups["after2"]:
            source = groups["before2"] or ""
            target = groups["after2"] or ""
        else:
            root = groups["root"] or ""
            rest = groups["rest"] or ""
            source = (root + (groups["before"] or "") + rest).replace("//", "/")
            target = (root + (groups["after"] or "") + rest).replace("//", "/")

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

    @staticmethod
    def _build_path(path):
        return ("".join([s.strip(" {}") for s in path])).replace("//", "/")

