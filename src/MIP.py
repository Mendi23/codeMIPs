'''
Created on Jun 7, 2015

@author: Ofra

Edited: Aug-Sep, 2018
@editors: Uriel, Mendi
'''
from itertools import combinations

import networkx as nx
import math


class Mip:
    """
    @:param alpha, beta1, beta2, gamma
    @:param decay
    """

    def __init__(self, alpha=0.2, beta1=0.6, beta2=0, gamma=0.2, similarityMetric="edge", decay=0.1):
        self.mip = nx.Graph()  # the representation of the MIP-Net network
        self.users = {}  # user ids
        self.objects = {}  # object ids
        self.iteration = 0
        self.lastID = -1
        # ASK: should the decay be dynamic and take into account both time and iterations?
        self.decay = decay  # determines how much to decay weights when there is not interaction between two nodes over time
        self.objectsInc = 1.0  # weight increment
        self.centrality = None  # centrality values of all nodes
        self.log = []  # log holds all the session data
        # ASK: are the parameter set or need learning?
        self.alpha = alpha  # weight given to the global importance (centrality) of the object
        self.beta1 = beta1  # weight given to the proximity between the user and the object
        self.beta2 = beta2  # weight given to the proximity between the focus object and the object
        self.gamma = gamma  # weight given to the extent of change
        self.nodeIDsToObjectsIds = {}  # dictionary mapping between ids of nodes and object ids
        self.nodeIDsToUsersIds = {}  # dictionary mapping between ids of nodes and user ids

        # ASK: what are the efffect of different similarityMetric?
        if similarityMetric == "edge":
            self.similarityMetric = self.edgeBasedProximity
        elif similarityMetric == "adamic":
            self.similarityMetric = self.adamicAdarProximity  # Adamic/Adar proximity
        elif similarityMetric == "simple":  # proximity = self.CFEC(userNodeID,obj) #cfec proximity
            self.similarityMetric = self.simpleProximity
        else:
            raise ValueError('Didn\'t defined a valid similarity metric')
        # how to measure proximity/similarity in the newtork

    def getLiveAos(self, user=None):  # generator of mip nodes that represent live object
        nodes = nx.descendants(self.mip, self.users[user]) if user is not None \
            else self.mip.nodes(data=True)

        yield from (node[0] for node in nodes \
                    if node[1]['node_type'] == 'object' and node[1]['deleted'] == 0)

    def addUser(self, user_name):
        if user_name not in self.users:
            self.lastID += 1
            self.users[user_name] = self.lastID
            # ASK: if a new user joins, should we make "last_visit" to be cuurent iteration instead of 0?
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

    def updateMIP(self, session):
        self.iteration += 1
        # initialize 'updated' attribute of all edges to false
        for edge in self.mip.edges_iter(data=True):
            edge[2]['updated'] = 0

        self.log.append(session)  # append session to log
        user = session.user

        if user not in self.users:  # add user of not exist
            self.addUser(user)
        user_node = self.users[user]
        self.mip.node[user_node]['last_visit'] = self.iteration
        # update MIP based on all actions
        changedAOs = []
        for act in session.actions:
            ao = act.ao
            if ao not in self.objects:
                nodeIdInMip = self.addObject(ao)
                act.updateMipNodeID(nodeIdInMip)
            ao_node = self.objects[ao]
            if self.iteration != self.mip.node[ao_node]['revisions'][-1]:
                self.mip.node[ao_node]['revisions'].append(self.iteration)  # add revision
            self.updateEdge(user_node, ao_node, 'u-ao', act.weightInc)
            changedAOs.append(ao_node)

            if act.actType == 'delete':  # label deleted objects as deleted
                self.mip.node[self.objects[act.ao]]['deleted'] = 1

        for node1, node2 in combinations(session.actions, 2):
            self.updateEdge(node1.ao, node2.ao, 'ao-ao', self.objectsInc)

        if self.decay > 0:
            for edge in self.mip.edges_iter(data=True):
                if edge[2]['updated'] == 0:
                    if edge[2]['edge_type'] == 'ao-ao':
                        if edge[0] in changedAOs or edge[1] in changedAOs:
                            edge[2]['weight'] = max(edge[2]['weight'] - self.decay, 0)
                    elif edge[2]['edge_type'] == 'u-ao':
                        if edge[0] == user_node or edge[1] == user_node:
                            edge[2]['weight'] = max(edge[2]['weight'] - self.decay, 0)
        # ASK: about centrality update and to-do
        #        self.centrality = nx.degree_centrality(self.mip)
        # #TODO: apriori importance for now is simply degree, consider reverting to more complex option

        if self.alpha > 0:
            try:
                self.centrality = nx.current_flow_betweenness_centrality(self.mip, True, weight='weight')
            except nx.NetworkXError:
                self.centrality = nx.degree_centrality(self.mip)
        else:
            self.centrality = nx.degree_centrality(self.mip)

    '''
    querying the mip net for the top ranked objects
    @user: the id of the user
    @infoLimit: communication budget (how many objects to share)
    @startRev: which revision to start from, 0 by default
    @node: the focus object (if given)
    @onlyChanged: whether to consider sharing only objects that were changed or also objects that might be relevant but
     haven't changed since the user last interacted with the system
    '''

    # TODO: FUNC
    def query(self, user, infoLimit, startRev=0, node=None, onlyChanged=True):  # to fit System API
        if node is None:  # rankedObjects = self.rankChangesForUser(user, startRev)
            rankedObjects = self.rankChangesForUserLastKnown(user, startRev, onlyChanged=onlyChanged)
        else:
            rankedObjects = self.rankAllGivenUserFocus(user, node, startRev, onlyChanged=onlyChanged)

        # commented out section below is the inclusion of one node that is *far* from the agent. probably doesn't make sense for the simulation now.
        #        if node is None:
        #            nodesToShare = rankedObjects[:infoLimit-1]
        #            if len(rankedObjects)>0:
        #                nodesToShare.append(rankedObjects[len(rankedObjects)-1])
        #        else:
        #            nodesToShare = rankedObjects[:infoLimit]

        nodesToShare = rankedObjects[:infoLimit]
        nodes = [i[0] for i in nodesToShare]
        #
        #        for node in nodes:
        #            if user not in self.users.keys():
        #                self.addUser(user)
        #            self.updateEdge(self.users[user], self.objects[node], 'u-ao', 0) #update the latest revision when the user was informed about the object

        return nodes

    # TODO: FUNC
    def queryList(self, user, infoLimit, startRev=0, node=None,
                  onlyChanged=True):  # to fit System API
        if node is None:
            #            rankedObjects = self.rankChangesForUser(user, startRev)
            rankedObjects = self.rankChangesForUserLastKnown(user, startRev,
                onlyChanged=onlyChanged)
        else:
            rankedObjects = self.rankAllGivenUserFocus(user, node, startRev,
                onlyChanged=onlyChanged)

        # commented out section below is the inclusion of one node that is *far* from the agent. probably doesn't make sense for the simulation now.
        #        if node is None:
        #            nodesToShare = rankedObjects[:infoLimit-1]
        #            if len(rankedObjects)>0:
        #                nodesToShare.append(rankedObjects[len(rankedObjects)-1])
        #        else:
        #            nodesToShare = rankedObjects[:infoLimit]

        nodesToShare = rankedObjects
        nodes = [i[0] for i in nodesToShare]
        #
        #        for node in nodes:
        #            if user not in self.users.keys():
        #                self.addUser(user)
        #            self.updateEdge(self.users[user], self.objects[node], 'u-ao', 0) #update the latest revision when the user was informed about the object

        return nodes

    '''
    MIP-update procedure, runs after each user session, updates weights between edges
    
    session:
    @user - name of user
    @actions - list of:
        action:
        @ao - id of the object the action was preformed on
        @actType - 'delete', 
        @updateMipNodeID - method which recieves the id of the object in the graph
        @weightInc - weight of the action (to be added to the edge)
    '''

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
        if increment > 0:
            self.mip[i1][i2]['updated'] = 1

    '''
    -----------------------------------------------------------------------------
    MIPs reasoning functions start
    -----------------------------------------------------------------------------
    '''

    '''
    Computes degree of interest between a user and an object
    gets as input the user id (might not yet be represented in mip) and obj node from MIP (not id)
    '''

    def DegreeOfInterestMIPs(self, user, obj):
        api_obj = self.centrality[obj]  # node centrality (apriori component)
        # compute proximity between user node and object node using Cycle-Free-Edge-Conductance from Koren et al. 2007 or Adamic/Adar
        proximity = 0.0
        if user in self.users and self.beta1 > 0:  # no point to compute proximity if beta1 is 0... (no weight)
            proximity = self.similarityMetric(self.users[user], obj)

        changeExtent = 0.0  # need to consider how frequently the object has been changed since user last known about it: user is userId (might not be in MIP), obj is object Node id
        if self.gamma > 0:
            changeExtent = self.changeExtent(user, obj)

        return self.alpha * api_obj + self.beta1 * proximity + self.gamma * changeExtent  # TODO: check that scales work out, otherwise need some normalization

    # TODO: FUNC
    def DegreeOfInterestMIPsFocus(self, user, obj, focus_obj):
        api_obj = self.centrality[obj]
        focus_proximity = 0.0
        try:
            if self.similarityMetric == 'simple':
                focus_proximity = self.simpleProximity(focus_obj, obj)  # node centrality (apriori component)
            else:
                focus_proximity = self.edgeBasedProximity(focus_obj, obj)
        except:
            print('here')

        # compute proximity between user node and object node using Cycle-Free-Edge-Conductance from Koren et al. 2007 or Adamic/Adar
        proximity = 0.0
        if ((user in self.users) & (
                self.beta1 > 0)):  # no point to compute proximity if beta1 is 0... (no weight)
            userNodeID = self.users[user]
            if self.similarityMetric == "adamic":
                proximity = self.adamicAdarProximity(userNodeID, obj)  # Adamic/Adar proximity
            elif self.similarityMetric == 'simple':
                #                proximity = self.CFEC(userNodeID,obj) #cfec proximity
                proximity = self.simpleProximity(userNodeID, obj)
            else:
                proximity = self.edgeBasedProximity(userNodeID, obj)
        changeExtent = 0.0
        if self.gamma > 0:  # need to consider how frequently the object has been changed since user last known about it: user is userId (might not be in MIP), obj is object Node id
            changeExtent = self.changeExtent(user, obj)

        return self.alpha * api_obj + self.beta1 * proximity + self.beta2 * focus_proximity + self.gamma * changeExtent  # TODO: check that scales work out, otherwise need some normalization

    '''
    computes Adamic/Adar proximity between nodes, adjusted to consider edge weights
    here's adamic/adar implementation in networkx. Modifying to consider edge weights            
    def predict(u, v):
        return sum(1 / math.log(G.degree(w))
                   for w in nx.common_neighbors(G, u, v))
    '''

    def adamicAdarProximity(self, s, t):  # s and t are the mip node IDs, NOT user/obj ids
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

    '''
    computes Cycle-Free-Edge-Conductance from Koren et al. 2007
    for each simple path, we compute the path probability (based on weights) 
    '''

    # TODO: FUNC
    def CFEC(self, s, t):
        R = nx.all_simple_paths(self.mip, s, t, cutoff=3)
        proximity = 0.0
        for r in R:
            PathWeight = self.mip.degree(r[0]) * (self.PathProb(r))  # check whether the degree makes a difference, or is it the same for all paths??
            proximity = proximity + PathWeight

        return proximity

    def PathProb(self, path):
        prob = 1.0
        for i in range(len(path) - 1):
            prob *= float(self.mip[path[i]][path[i + 1]]['weight']) / self.mip.degree(path[i])
        return prob

    '''
    computes the extent/frequency to which an object was changed since the last time the user was notified about it
    will be a component taken into account in degree of interest 
    '''

    # Quiestion about this function and it's relevant's for code:
    def changeExtent(self, userId, aoNode):
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

        # does number of chenges should be weighted by size of change???
        numOfChanges = sum(1 for i in revs if i > fromRevision)
        return numOfChanges / float((self.iteration - fromRevision))

    # ASK: what the fuck with the mountains of code I had to delete??
    # ASK: what should be the default limit?
    # ASK: should we allow repeated requests (meaning not discarding all changes as seen after the first request)
    '''
    rank all live objects based on DOI to predict what edits a user will make.
    NOTE: need to call this function with the mip prior to the users' edits!!!
    '''

    # ASK: comment from previous function. why need to call this function first?
    def rankObjects(self, user):
        if user not in self.users:
            print("this is a new user! getting default rankings")
            return self.getDefaultRankings()
        # ASK: if we do want to add "a runing changelog", need a basic value for new joinees. plus: new changes need to cancel old ones.

        tupledAos = ((ao, self.DegreeOfInterestMIPs(user, ao)) for ao in self.getLiveAos(user))
        return sorted(tupledAos, key=lambda x: x[1])

    def rankChanged(self, user, time=None):
        if user not in self.users:
            print("this is a new user! getting last changes")
            return self.getLastChanges()

        userNode = self.users[user]
        if time is None:
            time = self.mip.node[userNode]['last_visit']

        changedAos = ((ao, self.DegreeOfInterestMIPs(user, ao))
                      for ao in self.getLiveAos(user) if self.mip[ao]['revisions'][-1] > time)
        return sorted(changedAos, key=lambda x: x[1])

    # TODO: Implament
    def getLastChanges(self):
        pass

    # TODO: Implament
    def getDefaultRankings(self):
        pass

    # ASK: can't we use user focus at all?

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
