from src.MIP import Mip
from CSR import CsrFiles
from Factory import Provider
from prettytable import PrettyTable as pt
from DataModule.models import ChangeEnum
import matplotlib.pyplot as plt
from os import path, mkdir
from pyutils.file_paths import RESULTS_DIR

if __name__ == "__main__":
    repo = "urielha/heapdict"
    mip = Mip()
    csr = CsrFiles()
    p = Provider(0.8, repo)
    result_folder = path.join(RESULTS_DIR,repo.split('/')[-1])
    mkdir(result_folder)

    for i, commit in enumerate(p.X):
        mip.updateMIP(csr.commit_to_session(commit))

    for j, commit in enumerate(p.Y, i):
        mip.drawMip()
        plt.suptitle(f"graph before commit {j}", fontsize=14, fontweight='bold')

        session = csr.commit_to_session(commit)
        objects = session.get_session_objects(ChangeEnum.MODIFIED)

        pred_hits = []
        score = 0.0
        total_doi = 0.0

        for pred_o, pred_doi in mip.rankObjects(session.user):
            total_doi += pred_doi
            if pred_o in objects:
                score += pred_doi
                pred_hits.append(1)
            else:
                pred_hits.append(0)

        top_10 = sum(pred_hits[:10]) if len(pred_hits) >= 10 else -1
        top_5 = sum(pred_hits[:5]) if len(pred_hits) >= 5 else -1
        top_3 = sum(pred_hits[:3]) if len(pred_hits) >= 3 else -1
        plt.savefig(path.join(result_folder, str(j)))
        mip.updateMIP(session)
