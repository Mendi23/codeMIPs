from DataModule.DataQuery import Query
from Entities import Session
from MIP import Mip
from CSR import Csr


def main(repo_path):
    git = Query()
    graph = Mip()
    codeGraph = Csr()

    for commit in git.repo_iterate_commits(repo_path):
        # print(commit.sha)
        actions = list(codeGraph.apply_changes_from_commit(commit))
        graph.updateMIP(Session(commit.committer, actions, commit.date))


    for id, _ in graph.rankObjectsForUser("urielha"):
        print(codeGraph.mapping[id])


if __name__ == '__main__':
    main("urielha/SimpleObjectAppender")
