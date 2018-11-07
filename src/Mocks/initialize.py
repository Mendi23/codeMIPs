from src.MIP import Mip
from CSR import CsrFiles
from Factory import Provider
from prettytable import PrettyTable as pt
from DataModule.models import ChangeEnum
from os import path, mkdir
from pyutils.file_paths import RESULTS_DIR

if __name__ == "__main__":
    repo = "urielha/heapdict"
    mip = Mip()
    csr = CsrFiles()
    p = Provider(0.8, repo)

    result_folder = path.join(RESULTS_DIR,repo.split('/')[-1])
    if not path.exists(result_folder):
        mkdir(result_folder)

    table = pt(['commit', 'user', 'changed_objects', 'pred', 'score', 'top 3', 'top 5'])

    X, Y = p.X[0], p.Y[0]

    for i, commit in enumerate(X, 1):
        mip.updateMIP(csr.commit_to_session(commit))

    for j, commit in enumerate(Y, i):

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

        top_5 = sum(pred_hits[:5]) if len(pred_hits) >= 5 else -1
        top_3 = sum(pred_hits[:3]) if len(pred_hits) >= 3 else -1


        table.add_row([j, session.user.split('@', 1)[0],
                       objects, mip_ranking, score/total_doi, top_3, top_5])

        mip.drawMip(path.join(result_folder, str(j)), session.user, objects)
        mip.updateMIP(session)

    with open(path.join(result_folder, 'res.txt'), 'w') as f:
        f.write(str(table))
