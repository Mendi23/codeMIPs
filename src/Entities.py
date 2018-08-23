'''
Created on Jun 11, 2015

@author: Ofra

Edited: Aug-Sep, 2018
@editors: Uriel, Mendi
'''


class Session:
    def __init__(self, user, time):
        self.actions = []
        self.user = user
        self.time = time

    def addAction(self, action):
        self.actions.append(action)

    def __str__(self):
        toPrint = f"session at time {self.time} user = {self.user}\n"
        for act in self.actions:
            toPrint = toPrint + act + "\n"
        return toPrint


class Action:
    def __init__(self, ao, actType, weightInc=1):
        self.ao = ao
        self.actType = actType  # view, edit, add, delete
        self.weightInc = weightInc
        self.mipNodeID = -1

    def updateMipNodeID(self, id):
        self.mipNodeID = id

    def __str__(self):
        return f"ao = {self.ao}\nactType = {self.actType}weightInc = {self.weightInc}\nmipNodeID= {self.mipNodeID}\n"


if __name__ == '__main__':
    pass
