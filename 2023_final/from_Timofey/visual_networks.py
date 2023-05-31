from pyvis.network import Network
from help_functions import topologi_from_json_to_graph, topology_design


net = Network()  # создаём объект графа

nodes, edges = topologi_from_json_to_graph('2.json')
nodes_des = topology_design(nodes)
net.add_nodes(
    nodes_des[0],
    label=nodes_des[1],
    title=nodes_des[2],
    color=nodes_des[3]
)
# добавляем тот же список узлов, что и в предыдущем примере
net.add_edges(edges)

net.show('s.html')  # save visualization in 'graph.html'

# net.add_nodes(
#     [1, 2, 3],  # node ids
#     label=['#1', '#2', '#3'],  # node labels
#     # node titles (display on mouse hover)
#     title=['Just node', 'Just node', 'Just node'],
#     color=['#d47415', '#22b512', '#42adf5']  # node colors (HEX)
# )
# # добавляем тот же список узлов, что и в предыдущем примере
# net.add_edges([(1, 2), (1, 3), (2, 3)])
#
# net.show('s.html')  # save visualization in 'graph.html'
