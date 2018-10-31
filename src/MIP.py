'''
Created on Jun 7, 2015

@author: Ofra

Edited: Aug-Sep, 2018
@editors: Uriel, Mendi
'''
from itertools import combinations
from pyutils.my_sorted import MySorted
import networkx as nx
import math


# ASK: our proxy method for evaluation isn't good enough

class Mip:
    """
    @:param alpha, beta, gamma
    @:param user_decay, object_decay
    """

    def __init__(self, model_name=None, alpha=0.2, beta=0.6, gamma=0.2, user_decay=1.0, object_decay=1.0, similarityMetric="adamic"):
        self.mip = nx.Graph()  # the representation of the MIP-Net network
        self.users = {}  # user ids
        self.objects = {}  # object ids
        self.nodeIDsToObjectsIds = {}  # dictionary mapping between ids of nodes and object ids
        self.nodeIDsToUsersIds = {}  # dictionary mapping between ids of nodes and user ids
        self.iteration = 0
        self.lastID = -1
        self.name = model_name
        # ASK: what if we want real apriuti info? for example, the head node that need to be on top every time - move to CSR
        self.centrality = None
        self.set_params(alpha, beta, gamma, user_decay, object_decay, similarityMetric)

    def set_params(self, alpha=0.2, beta=0.6, gamma=0.2, user_decay=1.0, object_decay=1.0, similarityMetric="adamic"):
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
            raise ValueError('Didn\'t define a valid similarity metric')

    def getLiveAos(self, user=None, data=False):
        # generator of mip nodes that represent live object
        nodes = self.mip.nodes_iter(data=True) if user is None else \
            ((n, self.mip.node[n]) for n in self.mip.neighbors_iter(self.users[user]))
        liveNodes = ((n, att) for n, att in nodes if att['node_type'] == 'object' and not att['deleted'])
        yield from liveNodes if data else (n for n, _ in liveNodes)

    def addUser(self, user_name):
        if user_name not in self.users:
            self.lastID += 1
            self.users[user_name] = self.lastID
            attr = {'node_type': 'user',
                    'last_visit': -1}
            self.mip.add_node(self.lastID, **attr)
            self.nodeIDsToUsersIds[self.lastID] = user_name
        return self.users[user_name]

    def addObject(self, object_id):
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

    def updateMIP(self, session):
        self.iteration += 1
        self.centrality = None
        user = session.user
        user_node = self.addUser(user)
        user_att = self.mip.node[user_node]
        user_att['last_visit'] = self.iteration

        changedAOs = list()
        for act in session.actions:
            ao_node = self.addObject(act.ao)
            ao_att = self.mip.node[ao_node]
            # ASK: why do we need deleted and what to do if actualy deleted?
            # ASK: plus, right now is considering deleted for determening interest etc. can we use it?
            ao_att['deleted'] = False
            if act.actType == 'delete':  # label deleted objects as deleted
                ao_att['deleted'] = True

            assert ao_node not in changedAOs, "assuming only one action per object"
            ao_att['revisions'].append(self.iteration)  # add revision.
            changedAOs.append(ao_node)
            self.updateEdge(user_node, ao_node, 'u-ao', act.weightInc + self.userDecay)

        for n in self.getLiveAos(user):
            self.mip[user_node][n]['weight'] = max(0, self.mip[user_node][n]['weight'] - self.userDecay)

        # ASK: why do we need both increment between objects and decay for all others?
        # ASK why is the increment set to 1 and the decay vary?
        # ASK should the increment be by act.weightInc?
        # ASK: for example, if the action is "create", we want strong connnection
        for node1, node2 in combinations(changedAOs, 2):
            self.updateEdge(node1, node2, 'ao-ao', 1.0 + self.objectDecay)

        for _, _, att in self.mip.edges_iter(changedAOs, data=True):
            if att['edge_type'] == 'ao-ao':
                att['weight'] = max(0, att['weight'] - self.objectDecay)

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
    Proximity functions start
    -----------------------------------------------------------------------------
    '''

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
            total_rank = self.mip.degree(node, weight='weight')
            if weights != 0 and total_rank != 1:  # 0 essentially means no connection
                # ASK: need to be inf if 1? bu-g here in the original formula: proximity += (weights*(1/(math.log(self.mip.degree(node, weight = 'weight'))+0.00000000000000000000000001)))
                proximity += weights * 1 / math.log(total_rank)  # gives more weight to "rare" shared neighbors
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

    '''
    -----------------------------------------------------------------------------
    Proximity functions End
    -----------------------------------------------------------------------------
    '''

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
        if self.centrality is None:
            # ASK: need better centrality!!!
            self.centrality = nx.degree_centrality(self.mip)  # , weight='weight')

        api_obj = 0.0
        if self.alpha > 0:
            api_obj = self.centrality[obj]  # node centrality (apriori component)

        # compute proximity between user node and object node using Cycle-Free-Edge-Conductance from Koren et al. 2007 or Adamic/Adar
        proximity = 0.0
        if self.beta > 0 and user in self.users:  # no point to compute proximity if beta1 is 0... (no weight)
            proximity = self.similarityMetric(self.users[user], obj)

        changeExtent = 0.0  # need to consider how frequently the object has been changed since user last known about it: user is userId (might not be in MIP), obj is object Node id
        if self.gamma > 0:
            changeExtent = self.changeExtent(user, obj)

        return self.alpha * api_obj + self.beta * proximity + self.gamma * changeExtent
        # ASK: check that scales work out, otherwise need some normalization

    # ASK: how does changeExtend changes when lastvisit and lastknown are the same?
    # ASK: should time be a factor?
    def changeExtent(self, userId, aoNode):
        """
        computes the extent/frequency to which an object was changed since the last time the user was notified about it
        will be a component taken into account in degree of interest
        """
        fromRevision = 1  # in case user does not exist yet or has never known about this object, start from revision 0
        if userId in self.users and self.mip.has_edge(self.users[userId], aoNode):
            userNode = self.users[userId]
            fromRevision = self.mip[userNode][aoNode]['lastKnown']  # get the last time the user knew what the value of the object was

        revs = self.mip.node[aoNode]['revisions']
        numOfChanges = len(revs) - revs.index(fromRevision)
        return 0.0 if self.iteration == fromRevision \
            else numOfChanges / float(self.iteration - fromRevision)

    def rankObjects(self, user):
        tupledAos = ((self.nodeIDsToObjectsIds[ao], self.DegreeOfInterestMIPs(user, ao)) \
                     for ao in self.getLiveAos())
        return sorted(tupledAos, key=lambda x: x[1], reverse=True)

    def rankChanged(self, user, time=-1):
        if user in self.users and time == -1:
            time = self.mip.node[self.users[user]]['last_visit']
        return filter(lambda ao: self.mip.node[ao[0]]['revisions'][-1] > time, self.rankObjects(user))
    '''
    -----------------------------------------------------------------------------
    MIPs reasoning functions end
    -----------------------------------------------------------------------------
    '''

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
