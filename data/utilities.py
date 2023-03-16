import pandas as pd


def old_get_energy_loss(energy):
    a = min(abs(energy), 30)
    loss = ((abs(energy) * a) / 30) * 0.25
    return -loss


def get_energy_loss(energy):
    energy = abs(energy)
    coef_loss = ((energy / 50) ** 2.4) * 0.6

    return coef_loss


def get_column(name, file):
    values = list()
    dfs = list()
    df = pd.read_csv("forecast/" + file)
    df = df.fillna(0)
    df[df < 0] = 0
    # print(df[name])
    values.extend(df[name])
    return values


def get_forecasts(file):
    from collections import namedtuple
    Forecasts = namedtuple(
        "Forecasts", ("hospital", "factory", "houseA", "houseB", "sun", "wind")
    )
    rus_names = ["Солнце", "Ветер", "Дома А", "Дома Б", "Больницы", "Заводы"]
    df = pd.read_csv("../forecast/" + file)
    names = df.columns
    for name in rus_names:
        current_names = [na for na in names if name in na]

        print(current_names)
        print(df[current_names])


def mse(sample, truth):
    if len(sample) != len(truth):
        raise ValueError("Длины не совпадают")
    sum_error = 0
    for i in range(len(sample)):
        err = (sample[i] - truth[i]) ** 2
        sum_error += err
    return sum_error / len(sample)


def get_true_forecasts(samples, truth):
    return
    # truth_forecast = max(samples )


def get_wear_loss(wear):
    return (wear ** 2) * 0.5


def get_wear(energy):
    w = ((abs(energy) / 50) ** 1.9) / 2
    return w


def full_loss(wear, energy):
    energy = abs(energy)
    return (2 - (-get_wear_loss(wear) + 1) * (-get_energy_loss(energy) + 1)) * energy


def homeA_cons(price):
    return (0.82 * (5 - price) ** 2.6 if price < 5 else 0)


print(homeA_cons(4), homeA_cons(6) * 6)

print(get_wear_loss(0.5))
print(get_energy_loss(40))
print((2 - (-get_wear_loss(0.5) + 1) * (-get_energy_loss(40) + 1)) * 40)  # потребление с учётом всех потерь
print(get_wear(23))
# print((get_energy_loss(50) + 1) * 50)

# get_forecasts("forecast_2022-03-07T13.46_17.511Z.csv")
"""
# tree classifier to dict
# todo do tree regressor
def export_dict(clf, feature_names=None):
    tree = clf.tree_
    if feature_names is None:
        feature_names = range(clf.max_features_)

    # Build tree nodes
    tree_nodes = []
    for i in range(tree.node_count):
        if tree.children_left[i] == tree.children_right[i]:
            tree_nodes.append(clf.classes_[np.argmax(tree.value[i])])
        else:
            tree_nodes.append(
                {
                    "feature": feature_names[tree.feature[i]],
                    "value": tree.threshold[i],
                    "left": tree.children_left[i],
                    "right": tree.children_right[i],
                }
            )

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
        feature_names[i] if i != _tree.TREE_UNDEFINED else "undefined!" for i in tree_.feature
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
"""
