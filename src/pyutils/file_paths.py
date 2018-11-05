from os import path

_curPath = path.abspath(__file__)
_curDir = path.dirname(_curPath)
_rootSrc = path.abspath(path.join(_curDir, path.pardir))
_root = path.abspath(path.join(_rootSrc, path.pardir))

STORAGE_DIR = path.join(_root, "Storage")
REPOSITORIES_LIST_FILE = path.join(_root, "repositories.txt")
RESULTS_DIR = path.join(_root, "Results")
