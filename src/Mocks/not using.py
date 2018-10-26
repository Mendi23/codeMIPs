import networkx as nx


g = nx.Graph()
g.add_path(['a','b','c'])

for j in g.edges_iter('a', data=True):
    j[2]["aa"]=5

t = list(g.edges_iter(['a'], data=True))
print (t)
t[0][2]["hfj"] = 0

print(g['a'])

g.node['a']['xx'] = 5
t = g.node['a']
t['dfgf'] = 7
print(g.node['a'])
print(g.node['b'])
print(list(g.nodes_iter()))