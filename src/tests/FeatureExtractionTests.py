"""
Created on Sep 7, 2018

@authors: Uriel, Mendi
"""
import json
import unittest

import DataModule.models as Models
from CSR import CsrFiles
from DataModule.models import Commit, FileChangeset, ChangeEnum

class CsrTests(unittest.TestCase):

    def setUp(self):
        self.codeGraph = CsrFiles()

    def getCommit(self, filename, changetype, previous_filename=None):
        file = FileChangeset()
        file.changetype = changetype
        file.source = file.target = filename
        if previous_filename is not None:
            file.source = previous_filename

        commit = Commit()
        commit.files = [file]
        return commit

        # if status == "removed":
        #     previous_filename = filename
        #     filename = "/dev/null"
        #     content = "@@ -1,1 +0,0 @@\n" \
        #               "- bla"
        #
        # elif status == "added":
        #     previous_filename = "/dev/null"
        #     content = "@@ -0,0 +1,1 @@\n" \
        #               "+ bla"
        #
        # else: # modified or renamed
        #     content = "@@ -1,1 +1,1 @@\n" \
        #               "- bla\n" \
        #               "+ bli"
        #
        # commit = CommitPatch()
        # commit.patch = "diff --git a b\n" \
        #                f"--- {previous_filename}\n" \
        #                f"+++ {filename}\n" \
        #                + content

    def call_apply_changes(self, commit):
        return list(self.codeGraph.apply_changes_from_commit(commit))

    def call_apply_changes_one(self, commit):
        return self.call_apply_changes(commit)[0]

    def test_sanity(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.ADDED))
        self.assertEqual(res1.actType, "added")
        res2 = self.call_apply_changes_one(self.getCommit("2", ChangeEnum.RENAMED, "1"))
        self.assertEqual(res2.actType, "renamed")
        self.assertEqual(res1.ao, res2.ao)

        with self.assertRaises(KeyError):
            self.call_apply_changes_one(self.getCommit("1", ChangeEnum.DELETED))

        res2 = self.call_apply_changes_one(self.getCommit("2", ChangeEnum.DELETED))
        self.assertEqual(res2.actType, "removed")
        self.assertEqual(res1.ao, res2.ao)

    def test_rename_remove(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.ADDED))
        res2 = self.call_apply_changes_one(self.getCommit("2", ChangeEnum.RENAMED, "1"))
        self.assertEqual(res1.ao, res2.ao)
        self.assertEqual(res2.actType, "renamed")

        res2 = self.call_apply_changes_one(self.getCommit("3", ChangeEnum.RENAMED, "2"))
        self.assertEqual(res1.ao, res2.ao)

        res2 = self.call_apply_changes_one(self.getCommit("3", ChangeEnum.DELETED))
        self.assertEqual(res1.ao, res2.ao)
        self.assertEqual(res2.actType, "removed")

        res3 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.ADDED))
        self.assertNotEqual(res1.ao, res3.ao)

    def test_modified(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.ADDED))
        res2 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.MODIFIED))
        self.assertEqual(res1.ao, res2.ao)
        self.assertEqual(res2.actType, "modified")


if __name__ == '__main__':
    unittest.main()

