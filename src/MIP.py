'''
Created on Jun 7, 2015

@author: Ofra

Edited: Aug-nov, 2018
@editors: Uriel, Mendi
'''

from itertools import permutations
import math
from DataModule.models import ChangeEnum
from pyutils.utils import MySorted, DOI
import networkx as nx
import matplotlib.pyplot as plt
from numpy import array

OBJECT_DECAY = 1.0
USER_DECAY = 1.0
GAMMA = 0.2
BETA = 0.6
ALPHA = 0.2


class Mip:
    def __init__(self, model_name='__', alpha=ALPHA, beta=BETA, gamma=GAMMA,
                 user_decay=USER_DECAY, object_decay=OBJECT_DECAY):
        """
        :param model_name (optinal)
        :param alpha, beta, gamma - weights for computing distance to object.
        s.t. alpha+beta+gama = 1
        :param user_decay, object_decay - decay factors
        """
        self.mip = nx.Graph()  # the representation of the MIP-Net network
        self.users = {}  # mapping user_id -> node_id
        self.objects = {}  # mapping object -> node_id
        self.nodeIDsToObjectsIds = {}  # mapping node_id  -> object_id
        self.nodeIDsToUsersIds = {}  # mapping node_id  -> user_id

        self.iteration = 0  # counter for sessions omitted to graph
        self.lastID = -1  # integer id for nodes
        self.name = model_name  # for referencing
        self.centrality = None  # computed when when value is needed for DOI.

        self.set_params(alpha, beta, gamma, user_decay, object_decay)

    def set_params(self, alpha=ALPHA, beta=BETA, gamma=GAMMA,
                   user_decay=USER_DECAY, object_decay=OBJECT_DECAY):
        """
        :param alpha: weight of the global importance (centrality) of the object
        :param beta: weight of the proximity between the user and the object
        :param gamma: weight given to the changes since the user last visit
        :param user_decay: decay factor for u-ao edges
        :param object_decay: decay factor for ao-ao edges
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.userDecay = user_decay
        self.objectDecay = object_decay

    def getLiveAos(self, userNodeID=None):
        """
        :param userNodeID: only return live object connected to user (if not none)
        :return: list of mip nodes id that represent live object
        """
        nodes = self.mip.nodes if userNodeID is None \
            else self.mip.neighbors(userNodeID)

        return [n for n in nodes if self.mip.nodes[n]['node_type'] == 'object' \
                and self.mip.nodes[n]['deleted'] == False]

    def _addUser(self, user_name):
        """
        adding new user to the mip-graph
        if user exist, doesn't do anything
        :param user_name:
        :return: the user's node id
        """
        if user_name not in self.users:
            self.lastID += 1
            self.users[user_name] = self.lastID
            attr = {'node_type': 'user',
                    'last_visit': -1}
            self.mip.add_node(self.lastID, **attr)
            self.nodeIDsToUsersIds[self.lastID] = user_name
            self.centrality = None
        return self.users[user_name]

    def _addObject(self, object_id):
        """
        adding object user to the mip-graph
        if object exist, doesn't do anything
        :param object_id:
        :return: the object's node id
        """
        if object_id not in self.objects:
            self.lastID += 1
            self.objects[object_id] = self.lastID
            attr = {'node_type': 'object',
                    'deleted': False,
                    'revisions': MySorted()
                    }
            self.mip.add_node(self.lastID, **attr)
            self.nodeIDsToObjectsIds[self.lastID] = object_id
            self.centrality = None
        return self.objects[object_id]

    def getObjectNode(self, ao_id):
        return self.objects[ao_id]

    def getUserNode(self, user_id):
        return self.users[user_id]

    def updateMIP(self, session):
        """
        the heart and soul of the nodel. transform a session-object containing
        the fields:
            user - the user id
            actions - iterable of action-object containing the fields:
                ao - object id
                actType - type ChangeEnum
                weightInc - action weight
        see Entities.py for more info
        """
        self.iteration += 1
        self.centrality = None  # centrality values will change after the update
        user = session.user

        user_node = self._addUser(user)
        user_att = self.mip.nodes[user_node]

        user_att['last_visit'] = self.iteration

        changedAOs = {}
        for act in session.actions:
            ao_node = self._addObject(act.ao)
            ao_att = self.mip.nodes[ao_node]

            # label deleted objects as deleted
            ao_att['deleted'] = (act.actType == ChangeEnum.DELETED)

            assert ao_node not in changedAOs, \
                "assuming only one action per object in one session"

            ao_att['revisions'].append(self.iteration)  # add revision.
            changedAOs[ao_node] = act.weightInc
            # adding weights to edge between user and object
            self._updateEdge(user_node, ao_node, 'u-ao', act.weightInc)

        # adding weights to edge between two objects that appear in session
        # (total added is : sum of weightInc of both objects)
        for node1, node2 in permutations(changedAOs, 2):
            self._updateEdge(node1, node2, 'ao-ao', changedAOs[node1])

        # decay for edges between objects which only one of them is in session
        for node1, node2, att in self.mip.edges(changedAOs, data=True):
            if att['edge_type'] == 'ao-ao' and \
                    (node1 not in changedAOs or node2 not in changedAOs):
                att['weight'] = max(0, att['weight'] - self.objectDecay)

        to_remove = list()
        for n in self.mip.neighbors(user_node):
            if n not in changedAOs:
                att = self.mip[user_node][n]
                # decay for objects the user didn't interact with in the session
                att['weight'] = max(0, att['weight'] - self.userDecay)
                # if an object is deleted and weight of all connected edges is 0
                # - delete the node from graph
                if self.mip.nodes[n]['deleted'] == True and \
                        self.mip.degree(n, weight='weight') == 0:
                    to_remove.append(n)

        for n in to_remove:
            self.mip.remove_node(n)
            obj = self.nodeIDsToObjectsIds[n]
            del self.nodeIDsToObjectsIds[n]
            del self.objects[obj]

    def _updateEdge(self, i1, i2, edge_type, increment=1.0):
        if self.mip.has_edge(i1, i2):
            self.mip[i1][i2]['weight'] += increment
            # update last time user knew about object
            self.mip[i1][i2]['lastKnown'] = self.iteration
        else:  # this is the first interaction between user and object
            attr = {'edge_type': edge_type,
                    'weight': increment,
                    'lastKnown': self.iteration,
                    }
            self.mip.add_edge(i1, i2, **attr)

    def _simpleProximity(self, s, t):
        sharedWeight = 0.0
        for node in nx.common_neighbors(self.mip, s, t):
            # the weight of the path connecting s and t through the current node
            sharedWeight += self.mip[s][node]['weight'] + self.mip[t][node]['weight']
        if math.isclose(sharedWeight, 0, abs_tol=1e-09): return 0.0
        denominator = self.mip.degree(s, weight='weight') + \
                      self.mip.degree(t, weight='weight')
        return sharedWeight / denominator

    def DegreeOfInterestMIPs(self, userId, aoNode):
        """
        Compute degree of interest between user and object in the graph
        :param userId: user_id (might not yet be represented in mip)
        :param aoNode: object_node id
        :return: DOI(user,obj)
        """
        # only compute id needed and multiplying by the weights
        return (array([self.alpha, self.beta, self.gamma]) *
               self.getDoiComponents(userId, aoNode,
                   self.alpha > 0, self.beta > 0, self.gamma > 0)).sum()

    def getDoiComponents(self, userId, aoNode,
                         centrality=True, proximity=True, changeExtent=True):
        """
        if parameter is False, it's corresponding result will be 0
        :param userId: user_id (might not yet be represented in mip)
        :param aoNode:object_node id
        :param centrality:
        :param proximity:
        :param changeExtent:
        :return: np.array of (centrality,proximity,changeExtent)
        """

        assert self.mip.has_node(aoNode), 'aoNode must be a graph object node!'

        if self.centrality is None:  # graph has changes since last computed
            self.centrality = nx.degree_centrality(self.mip)

        a1, a2, a3 = 0, 0, 0

        if centrality:
            a1 = self.centrality[aoNode]

        if proximity and userId in self.users:
            a2 = self._simpleProximity(self.users[userId], aoNode)

        if changeExtent:
            a3 = self._changeExtent(userId, aoNode)

        return DOI(a1, a2, a3)

    def _changeExtent(self, userId, aoNode):
        """
        computes the extent/frequency to which an object was changed since
        the last time the user visited it.
        :param userId: user_id (might not yet be represented in mip)
        :param aoNode: object_node id
        :return: changeExtent(user,ao)
        """
        # in case user does not exist yet or has never known about this object,
        # start from the first iteration
        fromRevision = 1
        if userId in self.users and self.mip.has_edge(self.users[userId], aoNode):
            userNode = self.users[userId]
            # get the last time the user knew what the value of the object was
            fromRevision = self.mip[userNode][aoNode]['lastKnown']

        revs = self.mip.nodes[aoNode]['revisions']
        numOfChanges = len(revs) - revs.index(fromRevision)

        return 0.0 if self.iteration == fromRevision \
            else numOfChanges / float(self.iteration - fromRevision)

    def rankObjects(self, user):
        """
        :param user:
        :return: iterator of tuples (object_id, doi) of all object's in the graph
        sorted by the DOI of the user
        """
        nodesRanked = sorted(self._getObjectsDOI(user).items(),
            key=lambda x: x[1], reverse=True)
        return ((self.nodeIDsToObjectsIds[x[0]], float("{0:.3f}".format(x[1])))
                for x in nodesRanked)

    def rankChanged(self, user, time=-1):
        """
        :param user:
        :param time: if time=-1, return object's since the users' last visit
        :return: iterator of tuples (object_id, doi) of all object's since 'time'
        sorted by the DOI of the user
        """
        if user in self.users and time == -1:
            time = self.mip.nodes[self.users[user]]['last_visit']

        return filter(lambda ao: self.mip.nodes[ao[0]]['revisions'][-1] > time,
            self.rankObjects(user))

    def _getObjectsDOI(self, user):
        return {ao: self.DegreeOfInterestMIPs(user, ao) for ao in self.getLiveAos()}

    def drawMip(self, file_path, user_focus, objects_focus1, objects_focus2,
                neighbours=True):
        """
        saves an image of the *sub-graph* composed from a selected user and
        a group of objects.
        :param file_path: where to save the graph
        :param user_focus: the user which the DOI is in relation to
        :param objects_focus1: objects in this list will be highlighted in the graph
        :param objects_focus2: objects in this list will be added to the graph
        :param neighbours: weather to add the neighbours of the user_focus
        in the Mip-graph to the subgraph.
        """

        userNcolor = 'b'
        userNshape = '^'
        focususerNshape = 's'
        objNshape = 'o'
        nodeLsize = 6
        objNcmap = plt.cm.get_cmap("autumn")

        user_node = self._addUser(user_focus)
        object_nodes = [self._addObject(x) for x in objects_focus1]
        nodes = object_nodes + [user_node]
        if neighbours:
            nodes.extend(self.mip.neighbors(user_node))
        nodes.extend(self._addObject(x) for x in objects_focus2)
        subgraph = self.mip.subgraph(nodes)

        plt.figure(clear=True, frameon=False)
        plt.axis('off')
        layout = nx.shell_layout(subgraph)  # pick graph layout

        objects = []
        users = []
        objNcolor = []  # will be computed as color map from DOI
        objNline = []
        lables = {}

        for n in subgraph.nodes():
            if subgraph.nodes[n]['node_type'] == 'user':
                lables[n] = self.nodeIDsToUsersIds[n]
                if n is not user_node:
                    users.append(n)
            else:
                objects.append(n)
                lables[n] = self.nodeIDsToObjectsIds[n]
                objNcolor.append(self.DegreeOfInterestMIPs(user_focus, n))
                objNline.append(3.0 if n in object_nodes else 1.0)

        nx.draw_networkx_nodes(subgraph, pos=layout, nodelist=[user_node],
            edgecolors='black', node_color=userNcolor,
            node_shape=focususerNshape, label='focus_user_node')
        nx.draw_networkx_nodes(subgraph, pos=layout, nodelist=users,
            edgecolors='black', node_color=userNcolor,
            node_shape=userNshape, label='user_node')
        nx.draw_networkx_nodes(subgraph, pos=layout, nodelist=objects,
            node_color=objNcolor, node_shape=objNshape, cmap=objNcmap,
            linewidths=objNline, edgecolors='black', label='object_node')
        nx.draw_networkx_labels(subgraph, pos=layout,
            labels=lables, font_size=nodeLsize)

        edges = {(edge[0], edge[1]): edge[2]['weight']
                 for edge in subgraph.edges(data=True) if edge[2]['weight'] > 0}
        nx.draw_networkx_edges(subgraph, pos=layout, label='edge_weight',
            edgelist=edges.keys())
        nx.draw_networkx_edge_labels(subgraph, pos=layout, edge_labels=edges)

        plt.legend()
        plt.title(str(self))
        plt.suptitle(f"graph before commit {self.iteration+1}",
            fontsize=14, fontweight='bold')

        plt.savefig(file_path)
        plt.close()

    def __str__(self):
        return f"MIP_{self.name}__alpha={self.alpha}_beta={self.beta}_gamma={self.gamma}"


if __name__ == '__main__':
    pass
