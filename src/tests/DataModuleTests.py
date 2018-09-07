import os
import shutil
import unittest
from os import path

import DataModule.models as Models
import DataModule.DataQuery as DQ
from DataModule.utils import Storage, Gen
import itertools
import functools

STORAGE_DIR = path.join(path.pardir, "DataModule", "Storage")

class GenTests(unittest.TestCase):
    def test_generator(self):
        gen = Gen(10, range(100))
        c = functools.partial(next, itertools.count(0))
        for i in gen:
            self.assertEqual(i, c())

        for i in gen:
            self.assertEqual(i, c())

        for _ in gen:
            self.fail("should not reach here")

        self.assertEqual(100, c())


class StorageTests(unittest.TestCase):
    SOURCE_DIR = path.join(STORAGE_DIR, "nlohmann_json")
    DIR = "test_storage_dir"
    REPO = "repo_name"
    REPO_BACKUP = "repo_name_bckup"
    NON_EXISTS_REPO = "kuku_kuku_repo"

    @classmethod
    def setUpClass(cls):
        StorageTests.tearDownClass()
        os.mkdir(cls.DIR)
        shutil.copytree(cls.SOURCE_DIR,
                        path.join(cls.DIR, cls.REPO))

    @classmethod
    def tearDownClass(cls):
        if path.exists(cls.DIR):
            shutil.rmtree(cls.DIR)

    def setUp(self):
        self.storage = None
        shutil.copytree(path.join(self.DIR, self.REPO),
                        path.join(self.DIR, self.REPO_BACKUP))

    def tearDown(self):
        if self.storage:
            self.storage.dispose()
        # remove non_exists repo (if created)
        non_exists_repo = path.join(self.DIR, self.NON_EXISTS_REPO)
        if path.exists(non_exists_repo):
            shutil.rmtree(non_exists_repo)

        # return to backup repo
        shutil.rmtree(path.join(self.DIR, self.REPO))
        os.rename(path.join(self.DIR, self.REPO_BACKUP),
                  path.join(self.DIR, self.REPO))

    def test_sanity(self):
        self.storage = storage = Storage(self.DIR, self.REPO)
        self.assertEqual(storage.commits_len, 2663)

        # pages
        pages = storage.get_pages()
        self.assertGreater(len(pages), 0)
        pagenum, commits = pages.popitem()
        self.assertGreater(len(commits), 0)
        self.assertGreater(pagenum, 1)

    def test_add_pages(self):
        commit = Models.CommitPatch()
        commit.patch = "diff --git a/1 b/1\n" \
                        "--- /dev/null\n" \
                        "+++ b/bla.py\n" \
                        "@@ -0,0 +1,6 @@"

        self.storage = storage = Storage(self.DIR, self.NON_EXISTS_REPO)
        self.assertEqual(storage.commits_len, -1)
        storage.add_page(1, [commit])
        storage.commits_len = 1
        pages = storage.get_pages()
        self.assertIn(1, pages)
        self.assertEqual(len(pages[1]), 1)
        self.assertEquals(pages[1][0].patch, commit.patch)
        storage.dispose()

        self.storage = storage = Storage(self.DIR, self.NON_EXISTS_REPO)
        self.assertEqual(storage.commits_len, 1)
        n, commits = storage.get_pages().popitem()
        self.assertEqual(n, 1)
        self.assertEqual(commits[0].patch, commit.patch)
        storage.dispose()

if __name__ == '__main__':
    unittest.main()
