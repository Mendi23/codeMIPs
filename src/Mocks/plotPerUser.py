import sys

from src.MIP import Mip
from CSR import CsrFiles
from Factory import Provider
from prettytable import PrettyTable as pt
from DataModule.models import ChangeEnum
from os import path, mkdir
from pyutils.file_paths import RESULTS_DIR
import numpy as np
import pandas as pd


def make_result_dir(repo):
    result_folder = path.join(RESULTS_DIR, repo.split('/')[-1])
    if not path.exists(result_folder):
        mkdir(result_folder)
    return result_folder


if __name__ == "__main__":
    mip = Mip()
    csr = CsrFiles()
    p = Provider(1)

    table = pd.DataFrame(columns=["user", "commits", "accuracy"])

    for repo in p.X:
        make_result_dir(repo.name)
        for commit in repo:
            session = csr.commit_to_session(commit)
            objects = session.get_session_objects(ChangeEnum.MODIFIED)

            pred_hits = []
            score = 0.0
            total_doi = 0.0
            mip_ranking = list(mip.rankObjects(session.user))

            for (pred_o, pred_doi) in mip_ranking:
                total_doi += pred_doi
                if pred_o in objects:
                    score += pred_doi
                    pred_hits.append(1)
                else:
                    pred_hits.append(0)

            mip.updateMIP(session)

