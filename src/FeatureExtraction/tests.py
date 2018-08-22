from CSR import Csr
from DataModule.models import Commit, FileChangeset

def getCommit(filename, status, previous_filename=None):
    if previous_filename is None:
        previous_filename = filename
    commit = Commit()
    commit.files = [FileChangeset()]
    commit.files[0].filename = filename
    commit.files[0].previous_filename = previous_filename
    commit.files[0].status = status
    return commit

codeGraph = Csr()


res1 = list(codeGraph.apply_changes_from_commit(getCommit("1", "added")))[0]
assert res1.actType == "added"

res2 = list(codeGraph.apply_changes_from_commit(getCommit("2", "renamed", "1")))[0]
assert res1.ao == res2.ao
assert res2.actType == "renamed"

res2 = list(codeGraph.apply_changes_from_commit(getCommit("3", "renamed", "2")))[0]
assert res1.ao == res2.ao

res2 = list(codeGraph.apply_changes_from_commit(getCommit("3", "deleted")))[0]
assert res1.ao == res2.ao
assert res2.actType == "deleted"

res3 = list(codeGraph.apply_changes_from_commit(getCommit("1", "added")))[0]
assert res1.ao != res3.ao


print("All tests passed :)")