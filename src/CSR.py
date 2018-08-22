'''
Created on Aug 17, 2018

@authors: Uriel, Mendi
'''

import networkx as nx
from utils import hashing
from Entities import Action

class Csr:
    def __init__(self):
        self.csr = nx.Graph()
        self.mapping = hashing.MagicHash()

    def apply_changes_from_commit(self, commit):
        for file in commit.files:
            if file.status == 'deleted':
                objId = self.mapping.pop(file.filename)
            else:
                if file.status == 'renamed':
                    self.mapping.rename(file.previous_filename, file.filename)
                objId = self.mapping[file.filename]

            yield Action(objId, file.status)



