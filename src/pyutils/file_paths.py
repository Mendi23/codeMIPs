from os import path, mkdir

_curPath = path.abspath(__file__)
_curDir = path.dirname(_curPath)
_rootSrc = path.abspath(path.join(_curDir, path.pardir))
_root = path.abspath(path.join(_rootSrc, path.pardir))

STORAGE_DIR = path.join(_root, "Storage")
REPOSITORIES_LIST_FILE = path.join(_root, "src", "AnalysisModule", "repositories.txt")
RESULTS_DIR = path.join(_root, "Results")


def get_repo_result_dir(repo, params=None):
    result_folder = path.join(RESULTS_DIR, repo.name.split('/')[-1])
    if not path.exists(result_folder):
        mkdir(result_folder)

    if params is not None:
        result_folder = path.join(result_folder, "_".join(map(str, params)))

    if not path.exists(result_folder):
        mkdir(result_folder)

    return result_folder
