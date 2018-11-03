'''
Created on Jun 11, 2015

@author: Ofra

Edited: Aug-Sep, 2018
@editors: Uriel, Mendi
'''


class Session:
    def __init__(self, user, time, sessionWeight = 1.0):
        self.actions = []
        self.user = user
        self.time = time # Currently not used
        self.sessionWeight = sessionWeight

    def addAction(self, action):
        self.actions.append(action)

    def get_session_objects(self):
        '''
        :return: a list of object's modified in the session
        '''
        return [a.ao for a in self.actions]

    def __str__(self):
        toPrint = f"session at time {self.time} user = {self.user}\n"
        for act in self.actions:
            toPrint = toPrint + str(act) + "\n"
        return toPrint


class Action:
    def __init__(self, ao, actType, weightInc=1):
        self.ao = ao
        self.actType = actType  # view, edit, add, delete
        self.weightInc = weightInc
        self.mipNodeID = None # currently not aware of the mip node

    def __repr__(self):
        return f"< ao = {self.ao}, actType = {self.actType}, weightInc = {self.weightInc}, mipNodeID= {self.mipNodeID} >"

    def __hash__(self):
        return hash(hash(self.ao) * 10 + hash(self.actType) % 10)

    def __eq__(self, o: object) -> bool:
        return (
            o != None and
            isinstance(o, Action) and
            self.ao == o.ao and self.actType == o.actType
        )


if __name__ == '__main__':
    pass
