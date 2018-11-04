import networkx as nx


g = nx.Graph()
g.add_path(['a','b','c'])
g.add_node(1, time='5pm')
print(g.nodes) # just keys
print(g.nodes[1]) #just data
print((g.neighbors('b'))) # just keys
x = g.nodes[1]
x['col'] = 'red'
print(g.nodes[1]) # col also appear
print(g.nodes.data()) #tuple of (node, data)
print(g['b']) #tuple of (node, data) in neighbours
print(g.edges(['a','b'], data=True))
att = g['a']['b']
att['shade'] = 'black'
print(g.edges(['a','b'], data=True))