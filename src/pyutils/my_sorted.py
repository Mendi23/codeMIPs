
from sortedcontainers import SortedList

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