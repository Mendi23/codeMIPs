import functools
# import uritemplate, requests
from math import inf
from os.path import join as pathjoin
from typing import Dict, Iterator
from urllib.parse import urljoin
from git import Repo, Commit
from unidiff import PatchedFile, PatchSet
from DataModule.utils import *

FETCH_REPO = False
CACHE_THE_DATA = True
DEBUG_1 = False

PER_PAGE = 100

ORIGIN = "origin"
MASTER = "master"
BASE_URL = "https://github.com"


class GithubQuery:
    """
    Responsible for downloading the repository from Github
    and store it on the local storage.

    Usage:

    ```python
    query = GithubQuery.create(local_dir, repouri)
    query.num_of_commits()
    query.repo_iterate_commits()
    ```

    Params:
     * **local_dir** - name of the local directory for download repositories
       (the module will create subdirectory for each repo automaticlly so don't need to create directory for each repo)
     * **repouri** - the repository uri i.e. "torvalds/linux"

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

        if FETCH_REPO:
            print("[DataQuery] - fetch..")
            ret.repo.remotes.origin.fetch(MASTER)

        print("[DataQuery] - ready!")
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
    """
    This class is using the `GithubQuery` this class for downloading repos and:
     * Parse each commit to a known object (will be explained below)
     * Split to train/test (by ratio or explicit number)
     * Cache the extracted data for fast using later

    Usage:

    ```python
    data_extractor = DataExtractor(local_dir, repouri, ratio=0.8)
    # or
    data_extractor = DataExtractor(local_dir, repouri, k_commits=10)

    X = data_extractor.get_train()
    Y = data_extractor.get_test()
    ```

    Params:
     * **local_dir** and **repouri** as explained above
     * **ratio** - the ratio: (# train commits) / (# total commits)
     * **k_commits** - k commits = number of **test** commits.

    """
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
        return self._iterate_commits(storage, stop_at=self.first_slice)

    def get_test(self) -> Iterable[Models.Commit]:
        storage = self.initialize_repo_storage()
        return self._iterate_commits(storage, start_from=self.first_slice)

    def load_commits(self, storage: Storage):
        return storage.load_all()

    @staticmethod
    def _in_bounds(i, start, end):
        return start <= i < end

    def _iterate_commits(self, storage: Storage, start_from=0, stop_at=inf):
        query: GithubQuery = self.query

        skip_n = start_from
        if CACHE_THE_DATA:
            for i, commit in enumerate(self.load_commits(storage)):
                if i == 0:
                    print("SOME OF THE DATA WERE LOADED FROM CACHE!")
                if not self._in_bounds(i, start_from, stop_at):
                    continue
                yield commit
                skip_n += 1

        for i, commit in enumerate(query.repo_iterate_commits()):
            if i < skip_n or not self._in_bounds(i, start_from, stop_at): continue

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
