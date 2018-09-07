from CSR import Csr
from DataModule.models import Commit, FileChangeset

import unittest


class InitializeTests(unittest.TestCase):

    @staticmethod
    def getCommit(filename, status, previous_filename=None):
        if previous_filename is None:
            previous_filename = filename
        commit = Commit()
        commit.files = [FileChangeset()]
        commit.files[0].filename = filename
        commit.files[0].previous_filename = previous_filename
        commit.files[0].status = status
        return commit

    def call_apply_changes(self, commit):
        return list(self.codeGraph.apply_changes_from_commit(commit))

    def call_apply_changes_one(self, commit):
        return self.call_apply_changes(commit)[0]

    def setUp(self):
        self.codeGraph = Csr()

    def test_sanity(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", "added"))
        self.assertEqual(res1.actType, "added")
        res2 = self.call_apply_changes_one(self.getCommit("2", "renamed", "1"))
        self.assertEqual(res2.actType, "renamed")
        self.assertEqual(res1.ao, res2.ao)

        with self.assertRaises(KeyError):
            self.call_apply_changes_one(self.getCommit("1", "deleted"))
        res2 = self.call_apply_changes_one(self.getCommit("2", "deleted"))
        self.assertEqual(res2.actType, "deleted")
        self.assertEqual(res1.ao, res2.ao)

    def test_rename_and_delete(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", "added"))
        res2 = self.call_apply_changes_one(self.getCommit("2", "renamed", "1"))
        self.assertEqual(res1.ao, res2.ao)
        self.assertEqual(res2.actType, "renamed")

        res2 = self.call_apply_changes_one(self.getCommit("3", "renamed", "2"))
        self.assertEqual(res1.ao, res2.ao)

        res2 = self.call_apply_changes_one(self.getCommit("3", "deleted"))
        self.assertEqual(res1.ao, res2.ao)
        self.assertEqual(res2.actType, "deleted")

        res3 = self.call_apply_changes_one(self.getCommit("1", "added"))
        self.assertNotEqual(res1.ao, res3.ao)


if __name__ == '__main__':
    unittest.main()
