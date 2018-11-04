'''
Created on Jun 7, 2015

@author: Ofra

Edited: Aug-Sep, 2018
@editors: Uriel, Mendi
'''
from itertools import permutations
from pyutils.my_sorted import MySorted
import networkx as nx
import math
import matplotlib.pyplot as plt


class Mip:
    """
    @:param model_name (optinal)
    @:param alpha, beta, gamma - weights for computing distance to object. s.t. alpha+beta+gama = 1
    @:param user_decay, object_decay
    """

    def __init__(self, model_name=None, alpha=0.2, beta=0.6, gamma=0.2, user_decay=1.0, object_decay=1.0):
        self.mip = nx.Graph()  # the representation of the MIP-Net network
        self.users = {}  # user ids
        self.objects = {}  # object ids
        self.nodeIDsToObjectsIds = {}  # dictionary mapping between ids of nodes and object ids
        self.nodeIDsToUsersIds = {}  # dictionary mapping between ids of nodes and user ids

        self.iteration = 0  # counter for sessions omitted to graph
        self.lastID = -1  # integer id for nodes
        self.name = model_name  # for referencing
        self.centrality = None

        self.set_params(alpha, beta, gamma, user_decay, object_decay)

    def set_params(self, alpha=0.2, beta=0.6, gamma=0.2, user_decay=1.0, object_decay=1.0):
        self.alpha = alpha  # weight given to the global importance (centrality) of the object
        self.beta = beta  # weight given to the proximity between the user and the object
        self.gamma = gamma  # weight given to the extent of change
        self.userDecay = user_decay
        self.objectDecay = object_decay

    def getLiveAos(self, userID=None):
        """
        :param userID: if not none, only return live object connected to that user.
        :return: list of mip nodes id that represent live object
        """
        nodes = self.mip.nodes if userID is None else self.mip.neighbors(userID)
        return [n for n in nodes if self.mip.nodes[n]['node_type'] == 'object' and self.mip.nodes[n]['deleted'] == False]

    def _addUser(self, user_name):
        if user_name not in self.users:
            self.lastID += 1
            self.users[user_name] = self.lastID
            attr = {'node_type': 'user',
                    'last_visit': -1}
            self.mip.add_node(self.lastID, **attr)
            self.nodeIDsToUsersIds[self.lastID] = user_name
        return self.users[user_name]

    def _addObject(self, object_id):
        if object_id not in self.objects:
            self.lastID += 1
            self.objects[object_id] = self.lastID
            attr = {'node_type': 'object',
                    'deleted': False,
                    'revisions': MySorted()
                    }
            self.mip.add_node(self.lastID, **attr)
            self.nodeIDsToObjectsIds[self.lastID] = object_id
        return self.objects[object_id]

    def getObjectId(self, id):
        return self.objects[id]

    def getUserId(self, id):
        return self.users[id]

    def updateMIP(self, session):
        self.iteration += 1
        self.centrality = None
        user = session.user
        user_node = self._addUser(user)
        user_att = self.mip.nodes[user_node]
        user_att['last_visit'] = self.iteration

        changedAOs = {}
        for act in session.actions:
            ao_node = self._addObject(act.ao)
            ao_att = self.mip.nodes[ao_node]
            ao_att['deleted'] = (act.actType == 'delete')  # label deleted objects as deleted

            assert ao_node not in changedAOs, "assuming only one action per object in one session"
            ao_att['revisions'].append(self.iteration)  # add revision.
            changedAOs[ao_node] = act.weightInc
            self.updateEdge(user_node, ao_node, 'u-ao', act.weightInc)  # adding weights to edge between user and object

        # adding weights to edge between two objects that appear in session (total added to : weightInc of both objects)
        for node1, node2 in permutations(changedAOs, 2):
            self.updateEdge(node1, node2, 'ao-ao', changedAOs[node1])

        # decay for edges between objects that only one of them in session
        for node1, node2, att in self.mip.edges(changedAOs, data=True):
            if att['edge_type'] == 'ao-ao' and (node1 not in changedAOs or node2 not in changedAOs):
                att['weight'] = max(0, att['weight'] - self.objectDecay)

        for n in self.mip.neighbors(user_node):
            if n not in changedAOs:
                att = self.mip[user_node][n]
                att['weight'] = max(0, att['weight'] - self.userDecay)  # decay for objects the user didn't interact with in the session
                if self.mip.nodes[n]['deleted'] == True and self.mip.degree(n, weight='weight') == 0:
                    self.mip.remove_node(n)  # if an object is deleted and weight of all connected edges is 0 - delete the node from graph

    def updateEdge(self, i1, i2, edge_type, increment=1.0):
        if self.mip.has_edge(i1, i2):
            self.mip[i1][i2]['weight'] += increment
            self.mip[i1][i2]['lastKnown'] = self.iteration  # update last time user knew about object
        else:
            attr = {'edge_type': edge_type,
                    'weight': increment,
                    'lastKnown': self.iteration,
                    }
            self.mip.add_edge(i1, i2, **attr)

    def simpleProximity(self, s, t):  # s and t are the mip node IDs, NOT user/obj ids
        sharedWeight = 0.0
        for node in nx.common_neighbors(self.mip, s, t):
            sharedWeight += self.mip[s][node]['weight'] + self.mip[t][node]['weight']  # the weight of the path connecting s and t through the current node
        return sharedWeight / (self.mip.degree(s, weight='weight') + self.mip.degree(t, weight='weight'))

    def DegreeOfInterestMIPs(self, user, obj):
        """
        Computes degree of interest between a user and an object
        gets as input the user id (might not yet be represented in mip) and obj node from MIP (not id)
        """
        if self.centrality is None:
            self.centrality = nx.degree_centrality(self.mip)

        api_obj = 0.0
        if self.alpha > 0:
            api_obj = self.centrality[obj]  # node centrality (apriori component)

        proximity = 0.0
        if self.beta > 0 and user in self.users:
            proximity = self.simpleProximity(self.users[user], obj)

        changeExtent = 0.0  # need to consider how frequently the object has been changed since user last known about it: user is userId (might not be in MIP), obj is object Node id
        if self.gamma > 0:
            changeExtent = self.changeExtent(user, obj)

        return self.alpha * api_obj + self.beta * proximity + self.gamma * changeExtent

    def changeExtent(self, userId, aoNode):
        """
        computes the extent/frequency to which an object was changed since the last time the user was notified about it
        will be a component taken into account in degree of interest
        """
        fromRevision = 1  # in case user does not exist yet or has never known about this object, start from revision 0
        if userId in self.users and self.mip.has_edge(self.users[userId], aoNode):
            userNode = self.users[userId]
            fromRevision = self.mip[userNode][aoNode]['lastKnown']  # get the last time the user knew what the value of the object was

        revs = self.mip.nodes[aoNode]['revisions']
        numOfChanges = len(revs) - revs.index(fromRevision)
        return 0.0 if self.iteration == fromRevision \
            else numOfChanges / float(self.iteration - fromRevision)

    def rankObjects(self, user):
        tupledAos = ((self.nodeIDsToObjectsIds[ao], self.DegreeOfInterestMIPs(user, ao)) \
                     for ao in self.getLiveAos())
        return sorted(tupledAos, key=lambda x: x[1], reverse=True)

    def rankChanged(self, user, time=-1):
        if user in self.users and time == -1:
            time = self.mip.nodes[self.users[user]]['last_visit']
        return filter(lambda ao: self.mip.nodes[ao[0]]['revisions'][-1] > time, self.rankObjects(user))

    def drawMip(self):
        nx.draw(self.mip)
        plt.savefig("path.png")

    def __str__(self):
        return f"MIP_{self.alpha}_{self.beta}_{self.gamma}_{self.userDecay}_{self.objectDecay}"

    def createNodeLabels(self, nodeTypes='both'):
        labels = {}
        for node, data in self.mip.nodes(data=True):
            if data['node_type'] == 'user':
                if nodeTypes == 'user' or nodeTypes == 'both':
                    labels[node] = 'u' + self.nodeIDsToUsersIds[node]
            elif nodeTypes == 'object' or nodeTypes == 'both':
                labels[node] = 'o' + self.nodeIDsToObjectsIds[node]
        return labels

    def createEdgeLabels(self, nbunch=None):  # for network vidsualization
        labels = {}
        if nbunch is None:
            nbunch = self.mip.nodes()
        for n1, n2, data in self.mip.edges(data=True):
            if n1 in nbunch and n2 in nbunch:
                edge = (n1, n2)
                if data['weight'] > 0:
                    labels[edge] = data['weight']
        return labels


if __name__ == '__main__':
    pass
