from collections import deque, defaultdict, namedtuple
from functools import partial

from src.MIP import Mip
from CSR import CsrFiles
from Factory import Provider
from prettytable import PrettyTable as pt
from DataModule.models import ChangeEnum
from os import path
from pyutils.file_paths import get_repo_result_dir
import pandas as pd
import matplotlib.pyplot as plt

def draw_users(users_table, users_data, repo_name, result_folder):
    TOLERANCE = 10
    table = pd.DataFrame(data=list(users_table),
                         columns=["user", "commits", "accuracy", "top_3", "top_5"])

    for user in (u for u, v in users_data.items() if v["commits"] > TOLERANCE):
        u_table = table[table["user"] == user]
        if u_table.empty: continue
        plt.figure(clear=True)

        u_table = u_table.set_index("commits")
        ax = u_table.plot.line(
            figsize=(10, 6),
            title=f"Accuracy per commits | repo: {repo_name} | user: {user}",
        )
        xlabel = "Commit number (linear)"
        ax.set_xlabel(xlabel)
        commits_label = "MIP accuracy (doi/total_doi)"
        top3_label = "top_3 / total"
        top5_label = "top_5 / total"
        # ax.set_ylabel(ylabel)
        ax.legend([commits_label, top3_label, top5_label])

        filename = path.join(result_folder, f"{user}.png")
        plt.savefig(filename)
        plt.close()


def print_results(repo, visualize=False):
    mip = Mip(repo)
    csr = CsrFiles()
    result_folder = get_repo_result_dir(repo, [mip.alpha, mip.beta, mip.gamma])
    users_table = deque()
    users_data = defaultdict(
        lambda: {"commits": 0, "top3": 0, "top5": 0, "objects": 0, "score": 0.0})
    table_repo = pt(['commit', 'user', 'changed_objects', 'top 10 pred', 'score',
                     'top 3', 'top 5'])

    total, total_3, total_5 = 0, 0, 0
    for j, commit in enumerate(repo, 1):
        session = csr.commit_to_session(commit)
        if not session.actions: continue
        objects = session.get_session_objects(ChangeEnum.MODIFIED)
        username = session.user.split('@', 1)[0]
        if len(objects) > 0:
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

            num_objects = len(objects)
            total += num_objects

            top_3 = sum(pred_hits[:3])
            total_3 += top_3

            top_5 = sum(pred_hits[:5])
            total_5 += top_5

            prop_score = 0.0 if score is 0.0 else score / total_doi  # avoid devision by 0

            table_repo.add_row([j, username, objects,
                                "\n".join(str(a) for a in mip_ranking[:10]),
                                prop_score, top_3, top_5])

            users_data[username]["commits"] += 1
            users_data[username]["top3"] += top_3
            users_data[username]["top5"] += top_5
            users_data[username]["objects"] += num_objects
            users_data[username]["score"] += prop_score
            users_table.append({"user": username,
                         "commits": users_data[username]["commits"],
                         "accuracy": prop_score,
                         "top_3": top_3 / num_objects,
                         "top_5": top_5 / num_objects, })

            if visualize:
                ranked = [a[0] for a in mip_ranking[:10]]
                mip.drawMip(path.join(result_folder, str(j)), session.user,
                    objects, ranked, False)

                draw_users(users_table, users_data, repo.name, result_folder)

        mip.updateMIP(session)

    summarize_users = pt(['user', 'score', 'num_objects', 'top 3', 'top 5'])
    for user, data in users_data.items():
        summarize_users.add_row([user,
                                 data["score"],
                                 data["objects"],
                                 data["top3"],
                                 data["top5"],
                                 ])

    with open(path.join(result_folder, 'res.txt'), 'w') as f:
        f.write(table_repo.get_string(title=str(mip)))
        f.write(f"\nTotal of {total} objects were emitted\n"
                f"predicted {total_3} in the top-3\n"
                f"predicted {total_5} in the top-5\n")
        f.write("\n\nUsers Summary:\n")
        f.write(summarize_users.get_string())



if __name__ == "__main__":
    p = Provider(1)
    X, _ = p.X, p.Y

    for r in p.X:
        print_results(r, True)
