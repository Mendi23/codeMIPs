'''
Created on Jun 7, 2015

@author: Ofra
'''
import networkx as nx
import math

class Mip:
    def __init__(self, alpha = 0.2, beta1 = 0.6, beta2 = 0, gamma = 0.2, similarityMetric = "edge", decay = 0.1):
        self.mip = nx.Graph() #the representation of the MIP-Net network
        self.users = {} #user ids
        self.objects  = {} #object ids
        self.iteration = 0
        self.lastID = -1
        self.decay = decay #determines how much to decay weights when there is not interaction between two nodes over time
        self.objectsInc = 1.0 #weight increment
        self.centrality = None #centrality values of all nodes
        self.log = [] #log holds all the session data 
        self.alpha = alpha #weight given to the global importance (centrality) of the object
        self.beta1 = beta1 #weight given to the proximity between the user and the object
        self.beta2 = beta2 #weight given to the proximity between the focus object and the object
        self.gamma = gamma #weight given to the extent of change
        self.similarityMetric = similarityMetric #how to measure proximity/similarity in the newtork
        self.nodeIDsToObjectsIds = {} #dictionary mapping between ids of nodes and object ids
        self.nodeIDsToUsersIds = {} #dictionary mapping between ids of nodes and user ids
    
    def update(self, session): #to fit System API
        self.updateMIP(session)


    '''
    querying the mip net for the top ranked objects
    @user: the id of the user
    @infoLimit: communication budget (how many objects to share)
    @startRev: which revision to start from, 0 by default
    @node: the focus object (if given)
    @onlyChanged: whether to consider sharing only objects that were changed or also objects that might be relevant but
     haven't changed since the user last interacted with the system
    '''
    def query(self, user, infoLimit, startRev = 0, node = None, onlyChanged = True): #to fit System API
        if node is None:
#            rankedObjects = self.rankChangesForUser(user, startRev)
            rankedObjects = self.rankChangesForUserLastKnown(user, startRev, onlyChanged = onlyChanged)
        else:
            rankedObjects = self.rankAllGivenUserFocus(user, node, startRev, onlyChanged = onlyChanged)

#commented out section below is the inclusion of one node that is *far* from the agent. probably doesn't make sense for the simulation now.   
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
    
    def queryList(self, user, infoLimit, startRev = 0, node = None, onlyChanged = True): #to fit System API
        if node is None:
#            rankedObjects = self.rankChangesForUser(user, startRev)
            rankedObjects = self.rankChangesForUserLastKnown(user, startRev, onlyChanged = onlyChanged)
        else:
            rankedObjects = self.rankAllGivenUserFocus(user, node, startRev, onlyChanged = onlyChanged)

#commented out section below is the inclusion of one node that is *far* from the agent. probably doesn't make sense for the simulation now.   
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
    '''
    def updateMIP(self, session):
        #initialize 'updated' attribute of all edges to false
        for edge in self.mip.edges_iter(data=True):
            edge[2]['updated']=0
            
        self.log.append(session) #append session to log
        user = session.user
        if (user not in self.users):
            self.addUser(user)
        user_node = self.users[user]
        #update MIP based on all actions
        changedAOs=[]
        for act in session.actions:
            ao = act.ao
            if (ao not in self.objects):
                nodeIdInMip = self.addObject(ao)
                act.updateMipNodeID(nodeIdInMip)
            ao_node = self.objects[ao]
            if self.iteration not in self.mip.node[ao_node]['revisions']:
                self.mip.node[ao_node]['revisions'].append(self.iteration) #add revision
            # else:
            #     print 'interesting' DEBUG
            self.updateEdge(user_node, ao_node, 'u-ao', act.weightInc)
            changedAOs.append(ao_node)

            if act.actType == 'delete': #label deleted objects as deleted
                self.mip.node[self.objects[act.ao]]['deleted'] = 1
        
        for i in range(len(session.actions)-1):
            ao_node1 = self.objects[session.actions[i].ao]
            for j in range(i+1, len(session.actions)):
                ao_node2 = self.objects[session.actions[j].ao]
                if (ao_node1!=ao_node2):
                    self.updateEdge(ao_node1, ao_node2, 'ao-ao', self.objectsInc)
                
        #update weights between objects that user was informed about and objects that changed : this is relevant only if agent does not choose which nodes to change apriori
#        for i in range(len(session.actions)-1):
#            ao_node1 = self.objects[session.actions[i].ao]
#            for j in range(0, len(session.info)):
#                ao_node2 = self.objects[session.info[j]]
#                if (ao_node1!=ao_node2):
#                    self.updateEdge(ao_node1, ao_node2, 'ao-ao', self.objectsInc)
                        
        if self.decay>0:
            for edge in self.mip.edges_iter(data=True):
                if edge[2]['updated']==0:
                    if edge[2]['edge_type']=='ao-ao':
                        if ((edge[0] in changedAOs) | (edge[1] in changedAOs)):
                            edge[2]['weight'] = max(edge[2]['weight']-self.decay,0)
                    elif edge[2]['edge_type']=='u-ao':
                        if ((edge[0]==user_node) | (edge[1]==user_node)):
                            edge[2]['weight'] = max(edge[2]['weight']-self.decay,0)
        self.currentSession=session
#        print'updating'

#        self.centrality = nx.degree_centrality(self.mip) #TODO: apriori importance for now is simply degree, consider reverting to more complex option
        self.iteration = self.iteration+1
        if self.alpha>0:
            try:
                self.centrality = nx.current_flow_betweenness_centrality(self.mip,True, weight = 'weight')
            except:
                self.centrality = nx.degree_centrality(self.mip)
        else:
            self.centrality = nx.degree_centrality(self.mip)
        
    def addUser(self,user_name):
        if (user_name in self.users):
            return self.users[user_name]
        else:
            self.lastID=self.lastID+1
            self.users[user_name] = self.lastID
            attr = {}
            attr['node_type']='user'
            self.mip.add_node(self.lastID, attr)
            self.nodeIDsToUsersIds[self.lastID]=user_name
        return self.users[user_name]
            
    
    def addObject(self, object_id):
        if (object_id in self.objects):
            return self.objects[object_id]
        else:
            self.lastID=self.lastID+1
            self.objects[object_id] = self.lastID
            attr = {}
            attr['node_type']='object'
            attr['deleted'] = 0
            attr['revisions'] = []
            self.mip.add_node(self.lastID, attr)
            self.nodeIDsToObjectsIds[self.lastID]=object_id
        return self.objects[object_id]
        
           
    def updateEdge(self,i1,i2,edge_type,increment = 1):
        if self.mip.has_edge(i1, i2):
            self.mip[i1][i2]['weight']=self.mip[i1][i2]['weight']+increment
            self.mip[i1][i2]['lastKnown']=self.iteration #update last time user knew about object
#            print str(self.mip[i1][i2]['lastKnown'])
        else:
            attr = {}
            attr['edge_type']=edge_type
            attr['weight']=increment
            attr['lastKnown']=self.iteration #update last time user knew about object
            self.mip.add_edge(i1, i2, attr)
        if increment>0:
            self.mip[i1][i2]['updated']=1
        
    
    def getLiveAos(self): #return the mip nodes that represent live object
        liveObjects = []
        for node in self.mip.nodes(data = True):
            if node[1]['node_type']=='object':
                if node[1]['deleted']==0:
                    liveObjects.append(node[0])
        return liveObjects
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
     
        api_obj = self.centrality[obj]  #node centrality (apriori component)
       
        #compute proximity between user node and object node using Cycle-Free-Edge-Conductance from Koren et al. 2007 or Adamic/Adar
        proximity = 0.0
        if ((user in self.users) & (self.beta1>0)): #no point to compute proximity if beta1 is 0... (no weight)
            userNodeID = self.users[user]
            if self.similarityMetric == "adamic":
                proximity = self.adamicAdarProximity(userNodeID,obj) #Adamic/Adar proximity
            elif self.similarityMetric == "simple":
#                proximity = self.CFEC(userNodeID,obj) #cfec proximity
                proximity = self.simpleProximity(userNodeID,obj)
            else:
                proximity = self.edgeBasedProximity(userNodeID, obj)
        changeExtent = 0.0
        if self.gamma > 0:#need to consider how frequently the object has been changed since user last known about it: user is userId (might not be in MIP), obj is object Node id
            changeExtent = self.changeExtent(user, obj)


        return self.alpha*api_obj+self.beta1*proximity+self.gamma*changeExtent  #TODO: check that scales work out, otherwise need some normalization

    def DegreeOfInterestMIPsFocus(self, user, obj, focus_obj):
        
        api_obj = self.centrality[obj]
        focus_proximity = 0.0
        try:
            if self.similarityMetric=='simple':
                focus_proximity = self.simpleProximity(focus_obj,obj)  #node centrality (apriori component)
            else:
                focus_proximity = self.edgeBasedProximity(focus_obj,obj)            
        except:
            print 'here'
       
        #compute proximity between user node and object node using Cycle-Free-Edge-Conductance from Koren et al. 2007 or Adamic/Adar
        proximity = 0.0
        if ((user in self.users) & (self.beta1>0)): #no point to compute proximity if beta1 is 0... (no weight)
            userNodeID = self.users[user]
            if self.similarityMetric == "adamic":
                proximity = self.adamicAdarProximity(userNodeID,obj) #Adamic/Adar proximity
            elif self.similarityMetric=='simple':
#                proximity = self.CFEC(userNodeID,obj) #cfec proximity
                proximity = self.simpleProximity(userNodeID,obj)
            else:
                proximity = self.edgeBasedProximity(userNodeID,obj)
        changeExtent = 0.0
        if self.gamma > 0:#need to consider how frequently the object has been changed since user last known about it: user is userId (might not be in MIP), obj is object Node id
            changeExtent = self.changeExtent(user, obj)


        return self.alpha*api_obj+self.beta1*proximity+self.beta2*focus_proximity+self.gamma*changeExtent  #TODO: check that scales work out, otherwise need some normalization


    '''
    computes Adamic/Adar proximity between nodes, adjusted to consider edge weights
    here's adamic/adar implementation in networkx. Modifying to consider edge weights            
    def predict(u, v):
        return sum(1 / math.log(G.degree(w))
                   for w in nx.common_neighbors(G, u, v))
    '''
    def adamicAdarProximity(self, s, t): #s and t are the mip node IDs, NOT user/obj ids
        proximity = 0.0
        for node in nx.common_neighbors(self.mip, s, t):
            weights = self.mip[s][node]['weight'] + self.mip[t][node]['weight'] #the weight of the path connecting s and t through the current node
            if weights!=0: #0 essentially means no connection
#                print 'weights = '+str(weights)
#                print 'degree = '+str(self.mip.degree(node, weight = 'weight'))
                proximity = proximity + (weights*(1/(math.log(self.mip.degree(node, weight = 'weight'))+0.00000000000000000000000001))) #gives more weight to "rare" shared neighbors, adding small number to avoid dividing by zero
#                print 'proximity = '+str(proximity)
        return proximity    
    
    def simpleProximity(self, s, t): #s and t are the mip node IDs, NOT user/obj ids
        proximity = 0.0
        sharedWeight = 0.0
        for node in nx.common_neighbors(self.mip, s, t):
            sharedWeight = sharedWeight + self.mip[s][node]['weight'] + self.mip[t][node]['weight'] #the weight of the path connecting s and t through the current node
        proximity = sharedWeight/(self.mip.degree(s, weight = 'weight')+self.mip.degree(t, weight = 'weight')+0.000000000001)
        return proximity  
    
    
    def edgeBasedProximity(self,s,t, edgeWeight=0.7):
#        print 'correct function'
        simpleProximity = self.simpleProximity(s, t)
        edgeProximity=0.0
        if self.mip.has_edge(s, t):
            edgeProximity = self.mip[s][t]['weight']/self.mip.degree(s, weight = 'weight')
#            print 'there is an edge'
        return edgeWeight*edgeProximity+(1-edgeWeight)*simpleProximity 
    '''
    computes Cycle-Free-Edge-Conductance from Koren et al. 2007
    for each simple path, we compute the path probability (based on weights) 
    '''
    def CFEC(self,s,t):
        R = nx.all_simple_paths(self.mip, s, t, cutoff=3)
        proximity = 0.0
        for r in R:
            PathWeight = self.mip.degree(r[0])*(self.PathProb(r))  #check whether the degree makes a difference, or is it the same for all paths??
            proximity = proximity + PathWeight
            
            
        return proximity
        
            
    def PathProb(self, path):
        prob = 1.0
        for i in range(len(path)-1):
            prob = prob*(float(self.mip[path[i]][path[i+1]]['weight'])/self.mip.degree(path[i]))
#        print 'prob' + str(prob)
        return prob

    
    '''
    computes the extent/frequency to which an object was changed since the last time the user was notified about it
    will be a component taken into account in degree of interest 
    '''
    def changeExtent(self, userId, aoNode):
        fromRevision = 0 #in case user does not exist yet or has never known about this object, start from revision 0
        if userId in self.users.keys():
            userNode = self.users[userId]
            if self.mip.has_edge(userNode, aoNode):
                fromRevision = self.mip[userNode][aoNode]['lastKnown'] #get the last time the user knew what the value of the object was
        revs = self.mip.node[aoNode]['revisions']
        i = 0
        while revs[i]<fromRevision:
            i = i+1
            if  i>=len(revs)-1:
                break;
        
    
        if i<len(revs)-1:
            res =  (len(revs)-1-i)/float((self.iteration-fromRevision))
            if fromRevision==revs[len(revs)-1]:
                print 'hold on'
            return res
        else:
            return 0
    '''
    rank all live objects based on DOI to predict what edits a user will make.
    NOTE: need to call this function with the mip prior to the users' edits!!!
    '''
    def rankObjectsForUser(self, user):
        aoList = self.getLiveAos() #gets the MIP NODES that represent live objects
        notificationsList = [] #will hold list of objects, eventually sorted by interest
        for ao in aoList:
            doi = self.DegreeOfInterestMIPs(user, ao,self.centrality)  
            
            if len(notificationsList)==0:
                toAdd = []
                toAdd.append(self.nodeIDsToObjectsIds[ao]) #need to get the true object id to return (external to mip)
                toAdd.append(doi)
                notificationsList.append(toAdd)
            else:
                j = 0
                while ((doi<notificationsList[j][1])):
                    if j<len(notificationsList)-1:
                        j = j+1
                    else:
                        j=j+1
                        break
                toAdd = []
                toAdd.append(self.nodeIDsToObjectsIds[ao]) #need to get the true object id to return (external to mip)
                toAdd.append(doi)                  
                if (j<len(notificationsList)):
                    notificationsList.insert(j, toAdd)
                else:
                    notificationsList.append(toAdd)  
#        print 'notification list size = '+str(len(notificationsList))        
        return notificationsList
        
    '''
    rank only objects that have changed since the last time the user interacted (based on DOI to predict what edits a user will make.)
    NOTE: need to call this function with the mip prior to the users' edits!!!
    '''    
    def rankChangesForUser(self,user,time, onlySig = True):
        notificationsList = []
        checkedObjects = {}
        for i in range(time, len(self.log)): #this includes revision at time TIME and does  include last revision in MIP as we are querying before we update
#            print "time = "+str(i) + "author = "+self.log[i].user
                        
            session = self.log[i]
            for act in session.actions: 

                if ((act.actType != 'smallEdit') | (onlySig == False)):
                    inNotificationList = False
                    if (act.ao not in checkedObjects): #currently not giving more weight to the fact that an object was changed multiple times. --> removed because if there are both big and small changes etc...
                        #TODO: possibly add check whether the action is notifiable
                        
                        doi = self.DegreeOfInterestMIPs(user, self.objects[act.ao])
                        checkedObjects[act.ao] = doi
                    else:
                        doi = checkedObjects[act.ao] #already computed doi, don't recompute!
                        inNotificationList = True
                    #put in appropriate place in list based on doi
                    if len(notificationsList)==0:
                        toAdd = []
                        toAdd.append(act.ao)
                        toAdd.append(doi)
                        notificationsList.append(toAdd)
                    elif inNotificationList==False: #only add to list if wasn't already there (doi does not change)
                        j = 0

                        while ((doi<notificationsList[j][1])):
                            if j<len(notificationsList)-1:
                                j = j+1
                            else:
                                j=j+1
                                break
                        toAdd = []
                        toAdd.append(act.ao)
                        toAdd.append(doi)   
                     
                        if (j<len(notificationsList)):
                            notificationsList.insert(j, toAdd)
                        else:
                            notificationsList.append(toAdd)                        
        return notificationsList
    
    def rankChangesForUserLastKnown(self,user,time, onlyChanged = True, onlySig = True):
        aoList = self.getLiveAos() #gets the MIP NODES that represent live objects
        notificationsList = [] #will hold list of objects, eventually sorted by interest
        for ao in aoList:
            changeExtentSinceLastKnown = self.changeExtent(user, ao)
            if ((changeExtentSinceLastKnown != 0) | (onlyChanged==False)): #consider object only if it has changed at least once since agent last known about it
                doi = self.DegreeOfInterestMIPs(user, ao)  
                
                if len(notificationsList)==0:
                    toAdd = []
                    toAdd.append(self.nodeIDsToObjectsIds[ao]) #need to get the true object id to return (external to mip)
                    toAdd.append(doi)
                    notificationsList.append(toAdd)
                else:
                    j = 0
                    while ((doi<notificationsList[j][1])):
                        if j<len(notificationsList)-1:
                            j = j+1
                        else:
                            j=j+1
                            break
                    toAdd = []
                    toAdd.append(self.nodeIDsToObjectsIds[ao]) #need to get the true object id to return (external to mip)
                    toAdd.append(doi)                  
                    if (j<len(notificationsList)):
                        notificationsList.insert(j, toAdd)
                    else:
                        notificationsList.append(toAdd)  
#        print 'notification list size = '+str(len(notificationsList))        
        return notificationsList   
    
    
    def rankAllGivenUserFocus(self,user,focus_obj, time, onlyChanged = True): #TODO: check correctness and try at some point
        aoList = self.getLiveAos() #gets the MIP NODES that represent live objects
        notificationsList = [] #will hold list of objects, eventually sorted by interest
        if focus_obj in self.objects.keys():
            focus_ao = self.objects[focus_obj]
            for ao in aoList:
                changeExtentSinceLastKnown = self.changeExtent(user, ao)
                if ((changeExtentSinceLastKnown != 0) | (onlyChanged==False)): #consider object only if it has changed at least once since agent last known about it            
                    if (ao!=focus_ao): #consider object only if it has changed at least once since agent last known about it
                        doi = self.DegreeOfInterestMIPsFocus(user, ao, focus_ao)  
                        
                        if len(notificationsList)==0:
                            toAdd = []
                            toAdd.append(self.nodeIDsToObjectsIds[ao]) #need to get the true object id to return (external to mip)
                            toAdd.append(doi)
                            notificationsList.append(toAdd)
                        else:
                            j = 0
                            while ((doi<notificationsList[j][1])):
                                if j<len(notificationsList)-1:
                                    j = j+1
                                else:
                                    j=j+1
                                    break
                            toAdd = []
                            toAdd.append(self.nodeIDsToObjectsIds[ao]) #need to get the true object id to return (external to mip)
                            toAdd.append(doi)                  
                            if (j<len(notificationsList)):
                                notificationsList.insert(j, toAdd)
                            else:
                                notificationsList.append(toAdd) 
 
            return notificationsList
                    
        else:
            return self.rankChangesForUserLastKnown(user, time)
#        print 'notification list size = '+str(len(notificationsList))        
        
    
    def rankChangesGivenUserFocus(self,user,focus_obj, time, onlySig = True): #TODO: check correctness and try at some point
        notificationsList = []
        if focus_obj in self.objects.keys():
            focus_ao = self.objects[focus_obj]
        
            checkedObjects = {}
            for i in range(time, len(self.log)): #this includes revision at time TIME and does  include last revision in MIP as we are querying before we update
    #            print "time = "+str(i) + "author = "+self.log[i].user
                            
                session = self.log[i]
                for act in session.actions: 
    
                    if ((act.actType != 'smallEdit') | (onlySig == False)):
                        inNotificationList = False
                        if (act.ao not in checkedObjects): #currently not giving more weight to the fact that an object was changed multiple times. --> removed because if there are both big and small changes etc...
                            #TODO: possibly add check whether the action is notifiable
                            
                            doi = self.DegreeOfInterestMIPsFocus(user, self.objects[act.ao],focus_ao)
                            checkedObjects[act.ao] = doi
                        else:
                            doi = checkedObjects[act.ao] #already computed doi, don't recompute!
                            inNotificationList = True
                        #put in appropriate place in list based on doi
                        if len(notificationsList)==0:
                            toAdd = []
                            toAdd.append(act.ao)
                            toAdd.append(doi)
                            notificationsList.append(toAdd)
                        elif inNotificationList==False: #only add to list if wasn't already there (doi does not change)
                            j = 0
    
                            while ((doi<notificationsList[j][1])):
                                if j<len(notificationsList)-1:
                                    j = j+1
                                else:
                                    j=j+1
                                    break
                            toAdd = []
                            toAdd.append(act.ao)
                            toAdd.append(doi)   
                         
                            if (j<len(notificationsList)):
                                notificationsList.insert(j, toAdd)
                            else:
                                notificationsList.append(toAdd)                        
            return notificationsList   
        else:
            return self.rankChangesForUser(user, time, onlySig)
        
        


                 
                
    '''
    -----------------------------------------------------------------------------
    MIPs reasoning functions end
    -----------------------------------------------------------------------------
    '''
    def __str__(self):
        return "MIP_"+str(self.alpha)+"_"+str(self.beta1)+"_"+str(self.beta2)+"_"+str(self.gamma)+"_"+str(self.decay)+"_"+self.similarityMetric
        
    def createNodeLabels(self, nodeTypes = 'both'):
        labels = {}
        for node,data in self.mip.nodes(data = True):
            if data['node_type'] == 'user':
                if ((nodeTypes=='user') | (nodeTypes=='both')):
                    label = 'u'+str(self.nodeIDsToUsersIds[node])
                    labels[node] = label
            else:
                if ((nodeTypes=='object') | (nodeTypes=='both')):
                    label = 'o'+str(self.nodeIDsToObjectsIds[node])
                    labels[node] = label
        return labels
    
    def createEdgeLabels(self, nbunch = None): #for network vidsualization
        labels = {}
        if nbunch is None:
            nbunch = self.mip.nodes()
        for n1,n2,data in self.mip.edges(data=True):
            if ((n1 in nbunch) & (n2 in nbunch)):
                edge = (n1,n2)
                if data['weight']>0:
                    labels[edge] = data['weight']
        return labels
            
#    def drawMIP(self, filename):
#        
#        G = self.mip
#        
#        pos = nx.spring_layout(G)
#        self.pos = pos
#        self.drawn = True
#        nx.draw_networkx_nodes(G,self.pos,nodelist=self.nodeIDsToObjectsIds.keys(),node_size=300,font_size = 9, node_color='blue')
#        nx.draw_networkx_nodes(G,self.pos,nodelist=self.nodeIDsToUsersIds.keys(),node_size=300,font_size = 9,node_color='black')
#
#        nx.draw_networkx_edges(G,self.pos,edgelist=G.edges())
#        
#        nodeLabels = self.createNodeLabels()
#        nx.draw_networkx_labels(G,self.pos,labels = nodeLabels, font_color = "white")
#        
#        edgeLabels = self.createEdgeLabels()
#        nx.draw_networkx_edge_labels(G, pos, edgeLabels)
#
#
#        plt.draw()
#        plt.savefig(filename)
#        plt.clf()
#        plt.close()
#        
#    def drawMipObjects(self, filename):
#        G = self.mip
#        
#        pos = nx.spring_layout(G)
#        self.pos = pos
#        self.drawn = True
#        nx.draw_networkx_nodes(G,self.pos,nodelist=self.nodeIDsToObjectsIds.keys(),node_size=300,font_size = 9, node_color='blue')
#
#        nx.draw_networkx_edges(G,self.pos,edgelist=G.edges())
#        
#        nodeLabels = self.createNodeLabels(nodeTypes = 'object')
#        nx.draw_networkx_labels(G,self.pos,labels = nodeLabels, font_color = "white")
#        
#        edgeLabels = self.createEdgeLabels(nodeLabels.keys())
#        nx.draw_networkx_edge_labels(G, pos, edgeLabels,font_size = 7)
#
#
#        plt.draw()
#        plt.savefig(filename)
#        plt.clf()
#        plt.close()  
#        
#    def drawMipForUser(self, filename, user):
#        G = self.mip
#        
#        pos = nx.spring_layout(G)
#        self.pos = pos
#        self.drawn = True
#        nodesToDraw = nx.neighbors(G, self.users[user])
#        nodesToDraw.append(self.users[user])
#        nx.draw_networkx_nodes(G,self.pos,nodelist=nodesToDraw,node_size=300,font_size = 9, node_color='blue')
#
#        nx.draw_networkx_edges(G,self.pos,edgelist=G.edges())
#        
#        nodeLabels = self.createNodeLabels(nodeTypes = 'both')
#        nx.draw_networkx_labels(G,self.pos,labels = nodeLabels, font_color = "white")
#        
#        edgeLabels = self.createEdgeLabels(nodeLabels.keys())
#        nx.draw_networkx_edge_labels(G, pos, edgeLabels,font_size = 7)
#
#
#        plt.draw()
#        plt.savefig(filename)
#        plt.clf()
#        plt.close()          
              
if __name__ == '__main__':
    pass
