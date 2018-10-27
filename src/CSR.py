"""
Created on Aug 17, 2018

@authors: Uriel, Mendi
"""
import json

import networkx as nx
from pyutils import hashing
from Entities import Action
from unidiff import PatchedFile, PatchSet
import unidiff

import DataModule.models as Models


class CsrFiles:
    def __init__(self, patchSetAction=PatchSet):
        self.csr = nx.Graph()
        self.mapping = hashing.MagicHash()
        self.PatchSet = patchSetAction

    def apply_changes_from_commit(self, commit: Models.Commit):
        file: Models.FileChangeset = None  # for autocorrect
        for file in commit.files:
            if file.changetype == Models.ChangeEnum.ADDED:
                status = "added"
                objId = self.mapping[file.target]

            elif file.changetype == Models.ChangeEnum.MODIFIED:
                status = "modified"
                objId = self.mapping[file.target]

            elif file.changetype == Models.ChangeEnum.RENAMED:
                self.mapping.rename(file.source, file.target)
                status = "renamed"
                objId = self.mapping[file.target]

            elif file.changetype == Models.ChangeEnum.DELETED:
                status = "removed"
                objId = self.mapping.pop(file.source)

            else:
                raise ValueError(f"Unknown file status: {str(file)}")

            yield Action(objId, status)

class CsrCode:
    pass
