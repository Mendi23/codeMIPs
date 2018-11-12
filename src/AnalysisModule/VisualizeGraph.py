from collections import deque, defaultdict

from src.MIP import Mip
from CSR import CsrFiles
from Factory import Provider
from prettytable import PrettyTable as pt
from DataModule.models import ChangeEnum
from os import path
from pyutils.file_paths import get_repo_result_dir


def print_results(repo, visualize=False):
    mip = Mip(repo)
    csr = CsrFiles()
    result_folder = get_repo_result_dir(repo, [mip.alpha, mip.beta, mip.gamma])
    data = deque()
    users = defaultdict(int)
    table_repo = pt(['commit', 'user', 'changed_objects', 'top 10 pred', 'score',
                     'top 3', 'top 5'])
    table_users = pt(['user', 'score', 'num_objects', 'top 3', 'top 5'])

    total, total_3, total_5 = 0, 0, 0
    for j, commit in enumerate(X, 1):
        session = csr.commit_to_session(commit)
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

            users[username] += 1
            data.append({"user": username,
                         "commits": users[username],
                         "accuracy": prop_score,
                         "top_3": top_3 / num_objects,
                         "top_5": top_5 / num_objects, })

            if visualize:
                ranked = [a[0] for a in mip_ranking[:10]]
                mip.drawMip(path.join(result_folder, str(j)), session.user,
                    objects, ranked, False)
        mip.updateMIP(session)

    with open(path.join(result_folder, 'res.txt'), 'w') as f:
        f.write(table_repo.get_string(title=str(mip)))
        f.write(f"\nTotal of {total} objects were emitted\n"
                f"predicted {total_3} in the top-3\n"
                f"predicted {total_5} in the top-5\n")


if __name__ == "__main__":
    p = Provider(1)
    X, _ = p.X, p.Y

    for r in p.X:
        print_results(r)
