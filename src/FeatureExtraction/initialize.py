from DataModule.DataQuery import DataExtractor
from MIP import Mip
from Entities import Session
from CSR import Csr
from pyutils.file_paths import STORAGE_DIR


def main(repo_path):
    git = DataExtractor(STORAGE_DIR)
    graph = Mip()
    codeGraph = Csr()

    for commit in git.get_train_test_generator(repo_path):
        session = Session(commit.author.name, commit.date_str)
        for a in codeGraph.apply_changes_from_commit(commit):
            session.addAction(a)
        graph.updateMIP(session)


    for id, _ in graph.rankObjects("Uriel Hai"):
        print(codeGraph.mapping[id])


if __name__ == '__main__':
    main("urielha/heapdict")
