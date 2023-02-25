def get_energy_loss(energy):
    return energy * 0.1


# tree classifier to dict
# todo do tree regressor
def export_dict(clf, feature_names=None):
    tree = clf.tree_
    if feature_names is None:
        feature_names = range(clf.max_features_)

    # Build tree nodes
    tree_nodes = []
    for i in range(tree.node_count):
        if (tree.children_left[i] == tree.children_right[i]):
            tree_nodes.append(
                clf.classes_[np.argmax(tree.value[i])]
            )
        else:
            tree_nodes.append({
                "feature": feature_names[tree.feature[i]],
                "value": tree.threshold[i],
                "left": tree.children_left[i],
                "right": tree.children_right[i],
            })

    # Link tree nodes
    for node in tree_nodes:
        if isinstance(node, dict):
            node["left"] = tree_nodes[node["left"]]
        if isinstance(node, dict):
            node["right"] = tree_nodes[node["right"]]

    # Return root node
    return tree_nodes[0]


from sklearn.tree import _tree

def tree_to_code(tree, feature_names):
    tree_ = tree.tree_
    feature_name = [
        feature_names[i] if i != _tree.TREE_UNDEFINED else "undefined!"
        for i in tree_.feature
    ]
    print("def tree({}):".format(", ".join(feature_names)))

    def recurse(node, depth):
        indent = "  " * depth
        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            name = feature_name[node]
            threshold = tree_.threshold[node]
            print("{}if {} <= {}:".format(indent, name, threshold))
            recurse(tree_.children_left[node], depth + 1)
            print("{}else:  # if {} > {}".format(indent, name, threshold))
            recurse(tree_.children_right[node], depth + 1)
        else:
            print("{}return {}".format(indent, tree_.value[node]))

    recurse(0, 1)
