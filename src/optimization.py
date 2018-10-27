from scipy.optimize import minimize, Bounds
from src.MIP import Mip
from numpy import array, inf
from DataModule.DataQuery import DataExtractor
from pyutils.file_paths import STORAGE_DIR
from CSR import CsrFiles


def eval_func(x, *args) -> float:
    mip = args[0]
    mip.set_params(*x)
    return 0.0


if __name__ == "__main__":
    k=[1,3,10]
    res = []
    model = Mip()
    codeGraph = CsrFiles()

    for i in k:
        for X, y in get_split_sessions():
            pass


        x0 =  array((0.2, 0.6, 0.2, 1.0, 1.0))
        res.appent(minimize(eval_func, x0, (model,), bounds=Bounds(0, inf)))




    for commit in git.get_train_test_generator(repo_path):
        session = Session(commit.author.name, commit.date_str)
        for a in codeGraph.apply_changes_from_commit(commit):
            session.addAction(a)
        graph.updateMIP(session)


    for id, _ in graph.rankObjects("Uriel Hai"):
        print(codeGraph.mapping[id])

