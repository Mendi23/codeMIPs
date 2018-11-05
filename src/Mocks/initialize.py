from src.MIP import Mip
from CSR import CsrFiles
from Factory import Provider
from prettytable import PrettyTable as pt
from DataModule.models import ChangeEnum


if __name__ == "__main__":

    mip = Mip()
    csr = CsrFiles()
    p = Provider(0.8, "urielha/heapdict")
    for commit in p.X:
        mip.updateMIP(csr.commit_to_session(commit))

    t = pt(['user', 'score', 'top 3', 'top 5', 'top 10', 'all'])
    mip.drawMip()
    for commit in p.Y:
        session = csr.commit_to_session(commit)
        print(session)
        objects = set(session.get_session_objects(ChangeEnum.MODIFIED))
        pred_hits = []
        score = 0.0
        for pred_o, pred_doi in mip.rankObjects(session.user):
            if pred_o in objects:
                score += pred_doi
                pred_hits.append(1)
            else:
                pred_hits.append(0)
        top_10 = sum(pred_hits[:10]) if len(pred_hits) >= 10 else -1
        top_5 = sum(pred_hits[:5]) if len(pred_hits) >= 5 else -1
        top_3 = sum(pred_hits[:3]) if len(pred_hits) >= 3 else -1
        top_all = sum(pred_hits)
        t.add_row([session.user.split('@', 1)[0], score, top_3, top_5, top_10, top_all])
        # urielha 10
        # 7 8
        print(mip.mip.get_edge_data(10,8))
        print(f"predicted: {pred_hits}")
        mip.updateMIP(session)
        print("\n")
    print(t)


