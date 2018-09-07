import json
import unittest

import DataModule.models as Models
from CSR import Csr
from DataModule.models import Commit, FileChangeset

class CsrTests(unittest.TestCase):

    def setUp(self):
        self.codeGraph = Csr()

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

    def test_sanity(self):
        res1 = self.call_apply_changes_one(self.getCommit("1", "added"))
        self.assertEqual(res1.actType, "added")
        res2 = self.call_apply_changes_one(self.getCommit("2", "renamed", "1"))
        self.assertEqual(res2.actType, "renamed")
        self.assertEqual(res1.ao, res2.ao)

        with self.assertRaises(KeyError):
            self.call_apply_changes_one(self.getCommit("1", "removed"))
        with self.assertRaises(ValueError):
            self.call_apply_changes(self.getCommit("2", "_kuku_"))

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

    def test_bla(self):
        commit = Models.Commit.create(json.loads("""{
              "_name": "Commit",
              "sha": "ac5ff6585691f67f20419fe6c46f0df0e47e82b1",
              "url": "https://api.github.com/repos/nlohmann/json/commits/ac5ff6585691f67f20419fe6c46f0df0e47e82b1",
              "html_url": "https://github.com/nlohmann/json/commit/ac5ff6585691f67f20419fe6c46f0df0e47e82b1",
              "author": {
                "_name": "User",
                "name": "Niels",
                "email": "niels.lohmann@gmail.com"
              },
              "committer": {
                "_name": "User",
                "name": "Niels",
                "email": "niels.lohmann@gmail.com"
              },
              "message": "- bugfixing",
              "date": "2013-07-05T10:32:23Z",
              "files": [
                {
                  "_name": "FileChangeset",
                  "sha": "6139d9c87bd179057bd6778fe3c479710b2bcc73",
                  "filename": "src/JSON.cc",
                  "status": "modified",
                  "additions": 15,
                  "deletions": 5,
                  "changes": 20,
                  "patch": "H4sIAD/mhlsC/61TwU7jMBS89yvmhJxNW5pFwJJVpZz3wB44IhSlyUtqkdqR7S5bEP++dpwEUigFaZODFb+Z55k3TpJgdn55No3OEbbrJZIE2hRxrI3iosKvm9/XcZyaXUMi2xALkEuhDZ4mcK8vN5nSpPqV5etMfYMOECNtpGaLwMJnsE+62pYlKSwh6AEOd9sfVpNglhIiuvs5CVuw3arM2oLHmL78tlfP8E0caKDmzY51jClcD/j66SkUZQVKrqwr1yXLDSlfFPTXMId9Puj11axOPm157nWyQ3aH+n+wOs9Tu8eC45YTdxmuomn03V6GqzO32q0vu/6AwS2Fss0JUr5P6oQVZJVsuCB0/mQJLpqtgad6oKXPNdF9xRZTb5tLHcckCuuynbrmj5QaDCN1DEN1Xb3M9P3aR/1XVI2mmMtm1+mCkfAjP5j6KLBZf4xL4iUtj/l07OH7XdKhzVcuuYv/IrLxLxBeRDb+Hy7+P5IXe4mSUnJ0BbDRVRti+5uspKz3GP4Ii2gF8xLMJY/lcpDa19yjyGyVQJnVmjqPz5OwSybfKkXCuNi83VvXKgzvXpvV97yBURmvnbqHNTekmywnD7DfNaG/kW2B9X2DkZJjSg+oHSk+qtqj8Q/yCURBiwUAAA==",
                  "contents_url": "https://api.github.com/repos/nlohmann/json/contents/src/JSON.cc?ref=ac5ff6585691f67f20419fe6c46f0df0e47e82b1",
                  "raw_url": "https://github.com/nlohmann/json/raw/ac5ff6585691f67f20419fe6c46f0df0e47e82b1/src/JSON.cc"
                },
                {
                  "_name": "FileChangeset",
                  "sha": "ed2a775984f2c44f30ef8cfd3289b0db56d986e7",
                  "filename": "src/JSON.h",
                  "status": "added",
                  "additions": 1,
                  "deletions": 0,
                  "changes": 1,
                  "patch": "H4sIAD/mhlsC/3NwUNA1MjPRMVXQBlFmCg4OCsk5icXFCl7B/n4K1VwK6CA5I7FIIT65tKgoNa/EGru8lkJ8UmlaWmoRFvnizKrU+BKF+IL8YmsubVyyOal56SUZSNprgexaawBpm69PrwAAAA==",
                  "contents_url": "https://api.github.com/repos/nlohmann/json/contents/src/JSON.h?ref=ac5ff6585691f67f20419fe6c46f0df0e47e82b1",
                  "raw_url": "https://github.com/nlohmann/json/raw/ac5ff6585691f67f20419fe6c46f0df0e47e82b1/src/JSON.h"
                },
                {
                  "_name": "FileChangeset",
                  "sha": "7cecaec6618852e103b6288723f6658f753ebcb6",
                  "filename": "src/JSON.h",
                  "status": "removed",
                  "additions": 0,
                  "deletions": 17,
                  "changes": 17,
                  "patch": "",
                  "contents_url": "https://api.github.com/repos/nlohmann/json/contents/benchmark/JSON_benchmark.cc?ref=d1ac3d99385a2ff5e1a3f5c23f0e427983fb9dbe",
                  "raw_url": "https://github.com/nlohmann/json/raw/d1ac3d99385a2ff5e1a3f5c23f0e427983fb9dbe/benchmark/JSON_benchmark.cc"
                }
              ]
            }"""), True)
        print(commit)
        list(self.codeGraph.apply_changes_from_commit(commit))
        print("ha!")

if __name__ == '__main__':
    unittest.main()

