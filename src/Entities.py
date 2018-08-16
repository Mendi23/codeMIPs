'''
Created on Jun 11, 2015

@author: Ofra

Edited: Aug-Sep, 2018
@editors: Uriel, Mendi
'''

class Session:
    def __init__(self, user, revision, time):
        self.actions = revision
        self.user = user
        self.time = time #revision number

    def __str__(self):
        toPrint = f"session at time {str(self.time)} user = {str(self.user)}\n"
        for act in self.actions:
            toPrint = toPrint+str(act)+"\n"
        return toPrint
        
class Action:
    """
    weightInc = 1 is temporary value
    """
    def __init__(self, ao, actType, weightInc = 1):
        self.ao = ao
        self.actType = actType #view, edit, add, delete, rename
        self.weightInc = weightInc
        self.mipNodeID = -1
        
    def updateMipNodeID(self, _id):
        self.mipNodeID = _id
        
    def __str__(self):
        return f"ao = {self.ao}\nactType = {self.actType}weightInc = {self.weightInc}\nmipNodeID " \
               f"= {self.mipNodeID}\n"

# class Result:
#     def __init__(self, system, numIterations, graphState, percentColored):
#         self.system = system
#         self.iterations = numIterations
#         self.graphState = graphState
#         self.colored = percentColored
#
#     def __str__(self):
#         return "system = "+str(self.system) +"\n"+"iterations = "+str(self.iterations) +"\n" + "graph state = "+str(self.graphState) +"\n" + "percent colored = "+str(self.percentColored) +"\n"


if __name__ == '__main__':
    pass