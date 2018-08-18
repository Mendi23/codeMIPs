'''
Created on Aug 17, 2018

@authors: Uriel, Mendi
'''

import networkx as nx
import math
import pycallgraph as cg

class Csr:
    def __init__(self):
        self.csr = nx.Graph()
