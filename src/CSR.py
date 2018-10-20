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


class Csr:
    def __init__(self, patchSetAction=PatchSet):
        self.csr = nx.Graph()
        self.mapping = hashing.MagicHash()
        self.PatchSet = patchSetAction

    def apply_changes_from_commit(self, commit: Models.CommitPatch):
        patch = self.PatchSet(commit.patch)
        file: PatchedFile = None  # for autocorrect
        for file in patch:
            if file.is_added_file:
                status = "added"
                objId = self.mapping[file.target_file]

            elif file.is_modified_file:
                status = "modified"
                if file.source_file != file.target_file:
                    self.mapping.rename(file.source_file, file.target_file)
                    status = "renamed"
                objId = self.mapping[file.target_file]

            elif file.is_removed_file:
                status = "removed"
                objId = self.mapping.pop(file.source_file)

            else:
                raise ValueError(f"Unknown file status: {str(file)}")

            yield Action(objId, status)

