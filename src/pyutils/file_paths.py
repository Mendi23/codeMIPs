import os

_curPath = os.path.abspath(__file__)
_curDir = os.path.dirname(_curPath)
_root = os.path.abspath(os.path.join(_curDir, os.path.pardir))
EXAMPLE_PATH = os.path.join(_curDir, "example_code.c")
STORAGE_DIR = os.path.join(_root, os.path.pardir, "Storage")
