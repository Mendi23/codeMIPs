import sys
from src.MIP import Mip
from CSR import CsrFiles
from Factory import Provider
from prettytable import PrettyTable as pt
from DataModule.models import ChangeEnum
from os import path
from pyutils.file_paths import get_repo_result_dir

if __name__ == "__main__":
    repo = sys.argv[1]
    mip = Mip(repo)
    csr = CsrFiles()
    p = Provider(1, repo)
    result_folder = get_repo_result_dir(repo, [mip.alpha, mip.beta, mip.gamma])

    table = pt(['commit', 'user', 'changed_objects', 'top 10 pred', 'score',
                'top 3', 'top 5'])

    X, Y = p.X[0], p.Y[0]

    # i = 1
    # for i, commit in enumerate(X, 1):
    #     mip.updateMIP(csr.commit_to_session(commit))

    for j, commit in enumerate(X, 1):
        session = csr.commit_to_session(commit)
        objects = session.get_session_objects(ChangeEnum.MODIFIED)
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

            top_5 = sum(pred_hits[:5]) if len(pred_hits) >= 5 else None
            top_3 = sum(pred_hits[:3]) if len(pred_hits) >= 3 else None

            prop_score = 0.0 if score is 0.0 else score / total_doi #avoid devision by 0

            table.add_row([j, session.user.split('@', 1)[0],
                           objects, "\n".join(str(a) for a in mip_ranking[:10]),
                           prop_score, top_3, top_5])

            ranked = [a[0] for a in mip_ranking[:10]]

            mip.drawMip(path.join(result_folder, str(j)), session.user, objects, ranked, False)
        mip.updateMIP(session)

    with open(path.join(result_folder, 'res.txt'), 'w') as f:
        f.write(table.get_string(title=str(mip)))
