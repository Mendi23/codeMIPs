
from sortedcontainers import SortedList
from collections import namedtuple

class MySorted:

    def __init__(self):
        self.elements = SortedList()

    def index(self, val):
        if not self.elements or self.elements[0] >= val:
            return 0
        elif self.elements[-1] <= val:
            return len(self.elements)
        return self.elements.index(val)

    def append(self, val):
        self.elements.append(val)

    def __len__(self):
        return len(self.elements)


class mySumList:
    def __init__(self):
        self.sum = 0
        self.list = []

    def append(self, x):
        self.list.append(x)
        self.sum+=x

    def update(self, index, val):
        self.list[index] +=val
        self.sum+=val

DOI_Fields = ['centrality', 'proximity', 'changeExtent']

DOI = namedtuple('DOI',DOI_Fields)