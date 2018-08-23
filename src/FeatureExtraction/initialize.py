from DataModule.DataQuery import Query
from GeneralMIP import Mip
from Entities import Session
from CSR import Csr


def main(repo_path):
    git = Query()
    graph = Mip()
    codeGraph = Csr()

    for commit in git.repo_iterate_commits(repo_path):
        session = Session(commit.committer, commit.date)
        for a in codeGraph.apply_changes_from_commit(commit):
            session.addAction(a)
        graph.updateMIP(session)


    for id, _ in graph.rankObjectsForUser("urielha"):
        print(codeGraph.mapping[id])


if __name__ == '__main__':
    main("urielha/SimpleObjectAppender")
