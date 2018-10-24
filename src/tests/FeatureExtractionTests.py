"""
Created on Sep 7, 2018

@authors: Uriel, Mendi
"""
import json
import unittest

import DataModule.models as Models
from CSR import Csr
from DataModule.models import CommitPatch, FileChangeset

class CsrTests(unittest.TestCase):

    def setUp(self):
        self.codeGraph = Csr()

    def getCommit(self, filename, status, previous_filename=None):
        if previous_filename is None:
            previous_filename = filename

        if status == "removed":
            previous_filename = filename
            filename = "/dev/null"
            content = "@@ -1,1 +0,0 @@\n" \
                      "- bla"

        elif status == "added":
            previous_filename = "/dev/null"
            content = "@@ -0,0 +1,1 @@\n" \
                      "+ bla"

        else: # modified or renamed
            content = "@@ -1,1 +1,1 @@\n" \
                      "- bla\n" \
                      "+ bli"

        commit = CommitPatch()
        commit.patch = "diff --git a b\n" \
                       f"--- {previous_filename}\n" \
                       f"+++ {filename}\n" \
                       + content

        return commit

    def call_apply_changes(self, commit):
        return list(self.codeGraph.apply_changes_from_commit(commit))

    def call_apply_changes_one(self, commit):
        return self.call_apply_changes(commit)[0]

    def test_sanity(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", "added"))
        self.assertEqual(res1.actType, "added")
        res2 = self.call_apply_changes_one(self.getCommit("2", "renamed", "1"))
        self.assertEqual(res2.actType, "renamed")
        self.assertEqual(res1.ao, res2.ao)

        with self.assertRaises(KeyError):
            self.call_apply_changes_one(self.getCommit("1", "removed"))

        res2 = self.call_apply_changes_one(self.getCommit("2", "removed"))
        self.assertEqual(res2.actType, "removed")
        self.assertEqual(res1.ao, res2.ao)

    def test_rename_remove(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", "added"))
        res2 = self.call_apply_changes_one(self.getCommit("2", "renamed", "1"))
        self.assertEqual(res1.ao, res2.ao)
        self.assertEqual(res2.actType, "renamed")

        res2 = self.call_apply_changes_one(self.getCommit("3", "renamed", "2"))
        self.assertEqual(res1.ao, res2.ao)

        res2 = self.call_apply_changes_one(self.getCommit("3", "removed"))
        self.assertEqual(res1.ao, res2.ao)
        self.assertEqual(res2.actType, "removed")

        res3 = self.call_apply_changes_one(self.getCommit("1", "added"))
        self.assertNotEqual(res1.ao, res3.ao)

    def test_modified(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", "added"))
        res2 = self.call_apply_changes_one(self.getCommit("1", "modified"))
        self.assertEqual(res1.ao, res2.ao)
        self.assertEqual(res2.actType, "modified")


if __name__ == '__main__':
    unittest.main()

