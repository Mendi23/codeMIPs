from collections import defaultdict, deque
from os import path

import pandas as pd
import matplotlib.pyplot as plt

from CSR import CsrFiles, TooManyActionsError
from DataModule.models import ChangeEnum
from DataModule.Factory import Provider
from pyutils.file_paths import get_repo_result_dir
from src.MIP import Mip

TOLERANCE = 10


def process_repo(repo):
    mip = Mip()
    csr = CsrFiles()
    data = deque()
    users = defaultdict(int)
    directory = get_repo_result_dir(repo.name, [mip.alpha, mip.beta, mip.gamma])
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
        plt.figure(clear=True)

        ax = u_table.plot(
            kind='line', x='commits', y='accuracy',
            figsize=(10, 6),
            title=f"Accuracy per commits | repo: {repo.name} | user: {user}",
        )
        ylabel = "MIP accuracy (doi/total_doi)"
        xlabel = "Commit number (linear)"
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        filename = path.join(directory, f"{user}.png")
        plt.savefig(filename)
        plt.close()


if __name__ == "__main__":

    p = Provider(1)

    for repo in p.X:
        try:
            process_repo(repo)
        except TooManyActionsError:
            Provider.removeRepo(repo)
