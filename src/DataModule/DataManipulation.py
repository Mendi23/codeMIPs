import re
from unidiff import PatchSet


def create_changes_from_file(diff_str):
    pass
    regex = re.compile('(?<=#include\s\").*\"')
