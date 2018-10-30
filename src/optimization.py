from scipy.optimize import minimize, Bounds
from src.MIP import Mip
from numpy import array, inf
from DataModule.DataQuery import DataExtractor
from pyutils.file_paths import STORAGE_DIR
from CSR import CsrFiles
from Entities import Session
from Factory import Provider


def eval_func(x, *args) -> float:
    for mip in mip_models:
        mip.set_params(*x)

    for 




    return 0.0


if __name__ == "__main__":
    k = [10, 5, 3, 1]  # k must be in decending order
    p = Provider(k[0])

    mip_models = []

    for repo in p.X:
        mip_models.append(Mip(f"{repo.name}"))
        for commit in repo:
            session = Session(commit.author.name, commit.date_str)
            for action in commit:
                session.addAction(action)
            mip_models[-1].updateMIP(session)

    res = []


    for i, out_group in enumerate(p.Y):
        print(f"optimizing for k = {k[i]}:")
        x0 = array((0.2, 0.6, 0.2, 1.0, 1.0))
        res.append(minimize(eval_func, x0, (out_group,), bounds=Bounds(0, inf)))
        print (res[-1])
