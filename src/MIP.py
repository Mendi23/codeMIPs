'''
Created on Jun 7, 2015

@author: Ofra

Edited: Aug-Sep, 2018
@editors: Uriel, Mendi
'''
from itertools import combinations

import networkx as nx
import math

#ASK: do we really need decay as fixed value or dynamic? try without
class Mip:
    """
    @:param alpha, beta, gamma
    @:param user_decay, object_decay
    """

    def __init__(self, alpha=0.2, beta=0.6, gamma=0.2, similarityMetric="adamic", user_decay=1.0, object_decay=1.0):
        self.mip = nx.Graph()  # the representation of the MIP-Net network
        self.users = {}  # user ids
        self.objects = {}  # object ids
        self.nodeIDsToObjectsIds = {}  # dictionary mapping between ids of nodes and object ids
        self.nodeIDsToUsersIds = {}  # dictionary mapping between ids of nodes and user ids
        self.iteration = 0
        self.lastID = -1
        self.centrality = None  # centrality values of all nodes

        self.alpha = alpha  # weight given to the global importance (centrality) of the object
        self.beta = beta  # weight given to the proximity between the user and the object
        self.gamma = gamma  # weight given to the extent of change
        self.userDecay = user_decay
        self.objectDecay = object_decay

        # how to measure proximity/similarity in the newtork
        if similarityMetric == "edge":
            self.similarityMetric = self.edgeBasedProximity
        elif similarityMetric == "adamic":
            self.similarityMetric = self.adamicAdarProximity
        elif similarityMetric == "simple":
            self.similarityMetric = self.simpleProximity
        else:
            raise ValueError('Didn\'t defined a valid similarity metric')

    # ASK: what's up with deleted?
    def getLiveAos(self, user=None):  # generator of mip nodes that represent live object
        nodes = self.mip.neighbors(self.users[user]) if user is not None \
            else self.mip.nodes_iter()
        yield from (node for node in nodes \
                    if self.mip.node[node]['node_type'] == 'object' \
                    and not self.mip.node[node]['deleted'])

    def addUser(self, user_name):
        if user_name not in self.users:
            self.lastID += 1
            self.users[user_name] = self.lastID
            attr = {'node_type': 'user',
                    'last_visit': 0}
            self.mip.add_node(self.lastID, attr)
            self.nodeIDsToUsersIds[self.lastID] = user_name
        return self.users[user_name]

    def addObject(self, object_id):
        if object_id not in self.objects:
            self.lastID += 1
            self.objects[object_id] = self.lastID
            attr = {'node_type': 'object',
                    'deleted': False,
                    'revisions': []
                    }
            self.mip.add_node(self.lastID, attr)
            self.nodeIDsToObjectsIds[self.lastID] = object_id
        return self.objects[object_id]

    def getObjectId(self, id):
        return self.objects[id]

    def updateMIP(self, session):
        self.iteration += 1
        user = session.user
        user_node = self.addUser(user)
        self.mip.node[user_node]['last_visit'] = self.iteration

        changedAOs = list()
        for act in session.actions:
            ao_node = self.addObject(act.ao)
            changedAOs.append(ao_node)
            if ao_node not in changedAOs: # no need to check if we assume only one action per object
                self.mip.node[ao_node]['revisions'].append(self.iteration)  # add revision
            self.updateEdge(user_node, ao_node, 'u-ao', act.weightInc+self.userDecay)

        for ao in self.getLiveAos(user):
            after_decay = self.mip[user_node][ao]['weight'] - self.userDecay
            self.mip[user_node][ao]['weight'] = max(0, after_decay)

        for edge in self.mip.edges_iter(changedAOs):

        for node1, node2 in combinations(changedAOs, 2):
            self.updateEdge(node1, node2, 'ao-ao', 1.0)


        changedAOs = []
        for act in session.actions:
            ao = act.ao
            if ao not in self.objects:
                nodeIdInMip = self.addObject(ao)
                act.updateMipNodeID(nodeIdInMip)
            ao_node = self.objects[ao]
            if len(self.mip.node[ao_node]['revisions']) == 0 \
                    or self.iteration != self.mip.node[ao_node]['revisions'][-1]:
                self.mip.node[ao_node]['revisions'].append(self.iteration)  # add revision
            self.updateEdge(user_node, ao_node, 'u-ao', act.weightInc)
            changedAOs.append(ao_node)

            if act.actType == 'delete':  # label deleted objects as deleted
                self.mip.node[self.objects[act.ao]]['deleted'] = True

        for node1, node2 in combinations(session.actions, 2):
            self.updateEdge(node1.ao, node2.ao, 'ao-ao', 1.0)

        # ASK: here should appear updates based on code structure
        if self.decay > 0:
            for edge in self.mip.edges_iter(data=True):
                if edge[2]['updated'] == 0:
                    if edge[2]['edge_type'] == 'ao-ao':
                        if edge[0] in changedAOs or edge[1] in changedAOs:
                            edge[2]['weight'] = max(edge[2]['weight'] - self.decay, 0)
                    elif edge[2]['edge_type'] == 'u-ao':
                        if edge[0] == user_node or edge[1] == user_node:
                            edge[2]['weight'] = max(edge[2]['weight'] - self.decay, 0)

        if self.alpha > 0:
            try:
                self.centrality = nx.current_flow_betweenness_centrality(self.mip, True, weight='weight')
            except nx.NetworkXError:
                self.centrality = nx.degree_centrality(self.mip)
        else:
            self.centrality = nx.degree_centrality(self.mip)

    def updateEdge(self, i1, i2, edge_type, increment=1.0):
        if self.mip.has_edge(i1, i2):
            self.mip[i1][i2]['weight'] += increment
            self.mip[i1][i2]['lastKnown'] = self.iteration  # update last time user knew about object
        else:
            attr = {'edge_type': edge_type,
                    'weight': increment,
                    'lastKnown': self.iteration,
                    }
            self.mip.add_edge(i1, i2, attr)

    '''
    -----------------------------------------------------------------------------
    MIPs reasoning functions start
    -----------------------------------------------------------------------------
    '''

    def DegreeOfInterestMIPs(self, user, obj):
        """
        Computes degree of interest between a user and an object
        gets as input the user id (might not yet be represented in mip) and obj node from MIP (not id)
        """
        api_obj = self.centrality[obj]  # node centrality (apriori component)
        # compute proximity between user node and object node using Cycle-Free-Edge-Conductance from Koren et al. 2007 or Adamic/Adar
        proximity = 0.0
        if user in self.users and self.beta1 > 0:  # no point to compute proximity if beta1 is 0... (no weight)
            proximity = self.similarityMetric(self.users[user], obj)

        changeExtent = 0.0  # need to consider how frequently the object has been changed since user last known about it: user is userId (might not be in MIP), obj is object Node id
        if self.gamma > 0:
            changeExtent = self.changeExtent(user, obj)

        return self.alpha * api_obj + self.beta1 * proximity + self.gamma * changeExtent  # TODO: check that scales work out, otherwise need some normalization

    def adamicAdarProximity(self, s, t):  # s and t are the mip node IDs, NOT user/obj ids
        """
        computes Adamic/Adar proximity between nodes, adjusted to consider edge weights
        here's adamic/adar implementation in networkx. Modifying to consider edge weights
        def predict(u, v):
            return sum(1 / math.log(G.degree(w))
                       for w in nx.common_neighbors(G, u, v))
        """
        proximity = 0.0
        for node in nx.common_neighbors(self.mip, s, t):
            weights = self.mip[s][node]['weight'] + self.mip[t][node]['weight']  # the weight of the path connecting s and t through the current node
            if weights != 0:  # 0 essentially means no connection
                proximity += weights * 1 / math.log(self.mip.degree(node, weight='weight'))  # gives more weight to "rare" shared neighbors
        return proximity

    def simpleProximity(self, s, t):  # s and t are the mip node IDs, NOT user/obj ids
        sharedWeight = 0.0
        for node in nx.common_neighbors(self.mip, s, t):
            sharedWeight += self.mip[s][node]['weight'] + self.mip[t][node]['weight']  # the weight of the path connecting s and t through the current node
        return sharedWeight / (self.mip.degree(s, weight='weight') + self.mip.degree(t, weight='weight'))

    def edgeBasedProximity(self, s, t, edgeWeight=0.7):
        simpleProximity = self.simpleProximity(s, t)
        edgeProximity = 0.0
        if self.mip.has_edge(s, t):
            edgeProximity = self.mip[s][t]['weight'] / self.mip.degree(s, weight='weight')
        return edgeWeight * edgeProximity + (1 - edgeWeight) * simpleProximity

    def changeExtent(self, userId, aoNode):
        """
        computes the extent/frequency to which an object was changed since the last time the user was notified about it
        will be a component taken into account in degree of interest
        """
        fromRevision = 0  # in case user does not exist yet or has never known about this object, start from revision 0
        if userId in self.users and self.mip.has_edge(self.users[userId], aoNode):
            userNode = self.users[userId]
            if self.mip.has_edge(userNode, aoNode):
                fromRevision = self.mip[userNode][aoNode]['lastKnown']  # get the last time the user knew what the value of the object was
        # ASK: this all function seems to be wrong. lastKnown is noe last_visit and the calcaluations need adjusting
        revs = self.mip.node[aoNode]['revisions']

        # this message should't print. shouldn't we return 0?
        if revs[-1] == fromRevision:
            print(f"This code last changed by the user {userId} himself!")
            return 0

        numOfChanges = sum(1 for i in revs if i > fromRevision)
        return numOfChanges / float((self.iteration - fromRevision))

    def rankObjects(self, user):
        if user not in self.users:
            print(self.users)
            print("this is a new user! getting default rankings")
            return self.getDefaultRankings()

        tupledAos = ((self.nodeIDsToObjectsIds[ao], self.DegreeOfInterestMIPs(user, ao)) \
                     for ao in self.getLiveAos(user))
        return sorted(tupledAos, key=lambda x: x[1], reverse=True)

    def rankChanged(self, user, time=None):
        if user not in self.users:
            print("this is a new user! getting last changes")
            return self.getLastChanges()

        userNode = self.users[user]
        if time is None:
            time = self.mip.node[userNode]['last_visit']

        changedAos = ((self.nodeIDsToObjectsIds[ao], self.DegreeOfInterestMIPs(user, ao))
                      for ao in self.getLiveAos(user) if self.mip.node[ao]['revisions'][-1] > time)
        return sorted(changedAos, key=lambda x: x[1], reverse=True)

    # TODO: Implament
    def getLastChanges(self):
        pass

    # TODO: Implament
    def getDefaultRankings(self):
        pass

    '''
    -----------------------------------------------------------------------------
    MIPs reasoning functions end
    -----------------------------------------------------------------------------
    '''

    def __str__(self):
        return f"MIP_{self.alpha}_{self.beta1}_{self.beta2}_{self.gamma}_{self.decay}_{self.similarityMetric}"

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
