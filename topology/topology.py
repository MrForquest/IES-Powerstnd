import json

data = [
    {"address": "h1", "station": "M1", "line": 1},
    {"address": "t1", "station": "M1", "line": 2},
    {"address": "m2", "station": "M1", "line": 3},
    {"address": "h2", "station": "m2", "line": 1},
    {"address": "h3", "station": "m2", "line": 2},
]

file = open("topology.json", "w")
json.dump(data, file)
