from DataModule.DataQuery import DataExtractor
from MIP import Mip
from Entities import Session
from CSR import Csr


def main(repo_path):
    git = DataExtractor("..\\DataModule\\Storage")
    graph = Mip()
    codeGraph = Csr()

    for commit in git.get_train_test_generator(repo_path):
        session = Session(commit.committer.name, commit.date)
        for a in codeGraph.apply_changes_from_commit(commit):
            session.addAction(a)
        graph.updateMIP(session)


    for id, _ in graph.rankObjects("Uriel Hai"):
        print(codeGraph.mapping[id])


if __name__ == '__main__':
    main("urielha/heapdict")
