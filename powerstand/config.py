data = [
    {"address": "f1", "station": "M1", "line": 1},
    {"address": "f2", "station": "M1", "line": 2},
    {"address": "e1", "station": "M1", "line": 3},
    {"address": "f3", "station": "e1", "line": 1},
    {"address": "f5", "station": "e1", "line": 1},
    {"address": "f4", "station": "e1", "line": 2},
    {"address": "c3", "station": "e1", "line": 3},
]
config = {
    "topology": data,
    "forecasts": "forecasts-mar-09-3.csv",
    "gen_file": "gen-mar-09-3.csv",
    "prices": {"f1": 3, "f2": 3, "f3": 4, "f4": 4, "f5": 4, "f7": 2, "f8": 2,"c3":10},
    "mode": "predict_money",
    "panel_learn_files": (
        "gen-mar10-2.csv",
        "gen-mar10-1.csv",
        "gen-mar-09-3.csv",
        "gen-mar-09-2.csv",
        "gen-mar-09-1.csv",
        "game-mar08.csv",
    ),
    "penalty_mults": {"h": 3, "f": 8},
}
