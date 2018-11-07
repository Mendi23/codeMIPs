"""
Created on Sep 7, 2018

@authors: Uriel, Mendi
"""
import datetime
import unittest

from CSR import CsrFiles, SUPPORTED_FILE_TYPES
from DataModule.models import Commit, FileChangeset, ChangeEnum, User

class CsrTests(unittest.TestCase):

    def setUp(self):
        self.codeGraph = CsrFiles()

    def getCommit(self, filename, changetype, previous_filename=None):
        file = FileChangeset()
        file.changetype = changetype
        file.source = file.target = filename
        if previous_filename is not None:
            file.source = previous_filename

        suffix = "." + next(iter(SUPPORTED_FILE_TYPES))
        file.source += suffix
        file.target += suffix

        author = User()
        author.name = author.email = "bla"
        commit = Commit()
        commit.files = [file]
        commit.author = commit.committer = author
        commit.date_timestamp = datetime.datetime.now().timestamp()
        return commit

    def call_apply_changes(self, commit):
        return list(self.codeGraph.commit_to_session(commit).actions)

    def call_apply_changes_one(self, commit):
        return self.call_apply_changes(commit)[0]

    def test_sanity(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.ADDED))
        self.assertEqual(res1.actType, ChangeEnum.ADDED)
        self.call_apply_changes(self.getCommit("2", ChangeEnum.RENAMED, "1"))

        # with self.assertRaises(KeyError):
        #     self.call_apply_changes_one(self.getCommit("1", ChangeEnum.DELETED))
        res2 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.ADDED))
        self.assertNotEqual(res1.ao, res2.ao)

        res2 = self.call_apply_changes_one(self.getCommit("2", ChangeEnum.DELETED))
        self.assertEqual(res2.actType, ChangeEnum.DELETED)
        self.assertEqual(res1.ao, res2.ao)

    def test_rename_remove(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.ADDED))
        self.call_apply_changes(self.getCommit("2", ChangeEnum.RENAMED, "1"))

        self.call_apply_changes(self.getCommit("3", ChangeEnum.RENAMED, "2"))

        res2 = self.call_apply_changes_one(self.getCommit("3", ChangeEnum.DELETED))
        self.assertEqual(res1.ao, res2.ao)
        self.assertEqual(res2.actType, ChangeEnum.DELETED)

        res3 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.ADDED))
        self.assertNotEqual(res1.ao, res3.ao)

    def test_deleted(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.ADDED))
        res2 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.DELETED))
        res3 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.ADDED))
        self.assertEqual(res1.ao, res2.ao)
        self.assertEqual(res2.ao, res3.ao)

    def test_modified(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.ADDED))
        res2 = self.call_apply_changes_one(self.getCommit("1", ChangeEnum.MODIFIED))
        self.assertEqual(res1.ao, res2.ao)
        self.assertEqual(res2.actType, ChangeEnum.MODIFIED)


if __name__ == '__main__':
    unittest.main()

