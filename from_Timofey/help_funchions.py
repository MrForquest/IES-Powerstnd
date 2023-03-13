import json


class Station_m:
    def __init__(self, name):
        self.name = name
        self.lines = {1: [], 2: []}


class Station_M:
    def __init__(self, name):
        self.name = name
        self.lines = {1: [], 2: [], 3: []}


def topologi_from_json_to_graph(json_file):
    station_classes = []
    nodes = []
    edges = []

    # открытие .json файла
    with open('files/' + json_file) as json_f:
        data = json.load(json_f)

    topology = json_file

    # создание узлов
    for dict_ich in data:
        nodes.append(dict_ich['address'])
        nodes.append(dict_ich['station'])
    nodes = list(set(nodes))
    st_nodes = list(set([i for i in nodes if i[0] in ("m", "e", "M")]))
    gen_nodes = list(set([i for i in nodes if i[0] in ("s", "w")]))
    pr_nodes = list(set([i for i in nodes if i[0] not in ("m", "e", "M", "s", "w")]))

    # создание классов - подстанций
    for j in st_nodes:
        if j[0] == 'M':
            station_classes.append(Station_M(j))
        elif j[0] == 'm':
            station_classes.append(Station_m(j))

    # добавляем в классы подстанций объекты
    for dict_ich in data:
        station_class_x = list(filter(lambda x: x.name == dict_ich['station'], station_classes))[0]
        station_class_x.lines[dict_ich['line']].append(dict_ich['address'])

        # s = (dict_ich['address'], dict_ich['station'])
        # edges.append(s)

    # обработка для связей между узлами
    for station_class in station_classes:
        for dict_line_name in station_class.lines:
            list_connection = station_class.lines[dict_line_name]
            edges.append((station_class.name, list_connection[0])) if list_connection else None
            for i in range(len(list_connection) - 1):
                edges.append((list_connection[i], list_connection[i + 1]))
    return nodes, edges


def topology_design(nodes):
    c = []
    gen_nodes = list(set([i for i in nodes if i[0] in ("s", "w")]))
    pr_nodes = list(set([i for i in nodes if i[0] not in ("m", "e", "M", "s", "w")]))
    for i in nodes:
        if i[0] == 'M':
            c.append((i, i, 'Главная подстанция', '#d47415'))
        elif i[0] == 'm':
            c.append((i, i, 'Побочная подстанция', '#22b512'))
        elif i in pr_nodes:
            c.append((i, i, 'Сбыт', '#4a21b0'))
        elif i in gen_nodes:
            c.append((i, i, 'Генератор', '#e627a3'))
    return list(zip(*c))


print(topologi_from_json_to_graph('1.json'))
