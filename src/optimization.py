from scipy.optimize import minimize, Bounds
from src.MIP import Mip
from numpy import array, inf
from DataModule.DataQuery import DataExtractor
from pyutils.file_paths import STORAGE_DIR
from CSR import CsrFiles
from Entities import Session


def eval_func(x, *args) -> float:
    mip = args[0]
    mip.set_params(*x)
    return 0.0


if __name__ == "__main__":
    k=[10,5,3,1] # k must be in decending order
    p = Provider(k[0])

    for X, y in p:

    for i in k:
        for X, y in get_split_repos(i):
            for commit in X:
                session = Session(commit.author.name, commit.date_str)
                for a in codeGraph.apply_changes_from_commit(commit):
                    session.addAction(a)
                model.updateMIP(session)




    x0 =  array((0.2, 0.6, 0.2, 1.0, 1.0))
    res.append(minimize(eval_func, x0, (model,), bounds=Bounds(0, inf)))