from scipy.optimize import minimize, Bounds
from src.MIP import Mip
from numpy import array
from CSR import CsrFiles
from Factory import Provider
from copy import deepcopy
from prettytable import PrettyTable as pt
from DataModule.models import ChangeEnum


def verbose_print(s):
    pass  # print(s)


def eval_func(x, *args) -> float:
    mip, csr = deepcopy(args)
    verbose_print(f"current values: {x}")
    score = []
    for i, repo in enumerate(y):
        verbose_print(f"for repo: {repo.name}")
        mip[i].set_params(*x)
        score.append(0.0)
        t = pt(['user', 'score', 'top 3', 'top 5', 'top 10', 'total_objects'])
        for commit_i, commit in enumerate(repo, 1):
            session = csr[i].commit_to_session(commit)
            objects = set(session.get_session_objects(ChangeEnum.MODIFIED))
            pred_hits = []
            total_doi = 0.0

            for pred_o, pred_doi in mip[i].rankObjects(session.user):
                total_doi += pred_doi
                if pred_o in objects:
                    score[-1] += pred_doi
                    pred_hits.append(1)
                else:
                    pred_hits.append(0)

            top_10 = sum(pred_hits[:10]) if len(pred_hits) >= 10 else -1
            top_5 = sum(pred_hits[:5]) if len(pred_hits) >= 5 else -1
            top_3 = sum(pred_hits[:3]) if len(pred_hits) >= 3 else -1
            #            top_all = sum(pred_hits)
            score[-1] /= total_doi
            t.add_row([session.user.split('@', 1)[0], score[-1], top_3, top_5, top_10, len(objects)])
            mip[i].updateMIP(session)
        verbose_print(t)
        verbose_print(f"score for repo is: {score[-1]}")

    total = sum(score)
    verbose_print(f"--------------score is: {total}-------------------\n")
    return -total


if __name__ == "__main__":
    p = Provider(0.8)

    mip_models = []
    csr_models = []

    for repo in p.X:
        mip_models.append(Mip(f"{repo.name}"))
        csr_models.append(CsrFiles())
        for commit in repo:
            print(f"    files: {len(commit.files)}")
            mip_models[-1].updateMIP(csr_models[-1].commit_to_session(commit))

    x0 = array((0.2, 0.6, 0.2, 1.0, 1.0))
    y = list(p.Y)
    res = minimize(eval_func, x0, (mip_models, csr_models), bounds=Bounds(0, 2))

    print(res)
