'''
Created on Aug 17, 2018

@authors: Uriel, Mendi
'''
import json

import networkx as nx
from utils import hashing
from Entities import Action
from unidiff import PatchedFile, PatchSet
import unidiff

import DataModule.models as Models

class Csr:
    def __init__(self):
        self.csr = nx.Graph()
        self.mapping = hashing.MagicHash()

    def apply_changes_from_commit(self, commit):
        for file in commit.files:
            if file.status == 'added':
                if file.patch and len(file.patch) > 1:
                    patch = PatchSet(file.patch)
                    print(patch)
                objId = self.mapping[file.filename]
            elif file.status == 'modified':
                objId = self.mapping[file.filename]
            elif file.status == 'removed':
                objId = self.mapping.pop(file.filename)
            elif file.status == 'renamed':
                self.mapping.rename(file.previous_filename, file.filename)
                objId = self.mapping[file.filename]
            else:
                raise ValueError(f"Unknown file status: {file.status}")

            yield Action(objId, file.status)



