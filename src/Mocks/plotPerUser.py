from collections import defaultdict, deque
from os import path, mkdir

import pandas as pd
import matplotlib.pyplot as plt

from CSR import CsrFiles
from DataModule.models import ChangeEnum
from Factory import Provider
from pyutils.file_paths import RESULTS_DIR
from src.MIP import Mip


def make_result_dir(repo):
    result_folder = path.join(RESULTS_DIR, repo.split('/')[-1])
    if not path.exists(result_folder):
        mkdir(result_folder)
    return result_folder


if __name__ == "__main__":
    TOLERANCE = 10

    mip = Mip()
    csr = CsrFiles()
    p = Provider(1)

    for repo in p.X:
        data = deque()
        users = defaultdict(int)
        directory = make_result_dir(repo.name)

        for commit in repo:
            session = csr.commit_to_session(commit)
            objects = set(session.get_session_objects(ChangeEnum.MODIFIED))

            score = 0.0
            total_doi = 0.0
            mip_ranking = list(mip.rankObjects(session.user))

            for (pred_o, pred_doi) in mip_ranking:
                total_doi += pred_doi
                if pred_o in objects:
                    score += pred_doi

            mip.updateMIP(session)
            if total_doi > 0:
                user = session.user.split("@", 1)[0]
                users[user] += 1
                data.append({"user": user,
                             "commits": users[user],
                             "accuracy": score / total_doi})

        table = pd.DataFrame(data=list(data),
                             columns=["user", "commits", "accuracy"])
        for user in (u for u, v in users.items() if v > TOLERANCE):
            u_table = table[table["user"] == user]
            if u_table.empty: continue
            plt.figure(clear=True, figsize=(8,6))
            u_table.plot(kind='line', x='commits', y='accuracy')
            filename = path.join(directory, f"{user}.png")
            plt.savefig(filename)
