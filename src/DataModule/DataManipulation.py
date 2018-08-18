import re
from unidiff import PatchSet

from DataModule.models import FileChangeset


def create_changes_from_file(file : FileChangeset):
    """
    generator of Class objects, retrieved from changes fount in a file (FileChangeset)
    see doc of corresponding class for more details
    """


    regex = re.compile('(?<=#include\s\").*\"')
