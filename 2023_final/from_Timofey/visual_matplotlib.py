import matplotlib.pyplot as plt
import networkx as nx

from help_functions import topologi_from_json_to_graph

G = nx.Graph()

nodes, edges = topologi_from_json_to_graph('1.json')

G.add_nodes_from(nodes)
G.add_edges_from(edges)

nx.draw(G, with_labels=True, font_weight='bold')
plt.show()
