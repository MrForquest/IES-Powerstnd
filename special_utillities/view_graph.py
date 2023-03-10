import networkx as nx
import matplotlib.pyplot as plt

data = [
    {"address": "h1", "station": "M1", "line": 1},
    {"address": "s2", "station": "M1", "line": 2},
    {"address": "m2", "station": "M1", "line": 3},
    {"address": "h2", "station": "m2", "line": 1},
    {"address": "h3", "station": "m2", "line": 2},
    {"address": "h4", "station": "m2", "line": 2},
]
G = nx.Graph()

row_data = list()
for line in data:
    e = (line["station"], line["address"])
    G.add_edge(*e, name=line["address"], color="red")
nx.draw(G, with_labels=True, node_color="orange", node_size=2000)
plt.show()
