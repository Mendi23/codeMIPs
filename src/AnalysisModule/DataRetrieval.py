from sys import argv
from os import path
from CSR import CsrFiles
from DataModule.models import ChangeEnum
from Factory import Provider
from MIP import Mip
from pyutils.utils import DOI_Fields
from pyutils.file_paths import get_repo_result_dir
import pandas as pd

def retreive_data(repo):
    mip = Mip(repo.name)
    csr = CsrFiles()

    data = {'user': [],
            'modified': [],
            'added': [],
            }

    for field in DOI_Fields:
        data[f"modified_{field}"] = []
        data[f"all_{field}"] = []

    for commit in repo:
        session = csr.commit_to_session(commit)
        if session.actions:
            data['user'].append(session.user.split('@', 1)[0])
            data['added'].append(session.get_session_objects(ChangeEnum.ADDED))
            data['modified'].append(session.get_session_objects(ChangeEnum.MODIFIED))

            for field in DOI_Fields:
                data[f"modified_{field}"].append(0)
                data[f"all_{field}"].append(0)

            for node, obj in mip.nodeIDsToObjectsIds.items():
                doi = mip.getDoiComponents(session.user, node)

                for index, field in enumerate(DOI_Fields):
                    data[f"all_{field}"][-1]+= doi[index]

                    if obj in data['modified'][-1]:
                        data[f"modified_{field}"][-1] +=doi[index]

            mip.updateMIP(session)

    data['user'].append('@total@')
    data['modified'].append(list())
    data['added'].append(list())
    for field in DOI_Fields:
        data[f"modified_{field}"].append(sum(data[f"modified_{field}"]))
        data[f"all_{field}"].append(sum(data[f"all_{field}"]))

    return pd.DataFrame.from_dict(data)


if __name__ == "__main__":
    p = Provider(1)
    X, _ = p.X, p.Y
    for repo in p.X:
        with open(path.join(get_repo_result_dir(repo.name), 'data.txt'), 'w') as f:
            retreive_data(repo).to_string(f)
