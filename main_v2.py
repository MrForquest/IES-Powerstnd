import json
from data.powerstand import Powerstand

data = [{"address": "h1", "station": "M1", "line": 1},
        {"address": "s2", "station": "M1", "line": 2},
        {"address": "m2", "station": "M1", "line": 3},
        {"address": "h2", "station": "m2", "line": 1},
        {"address": "h3", "station": "m2", "line": 2},
        {"address": "h4", "station": "m2", "line": 2}]



# mode - "predict_money"(Дима)/"test_strategy"(Серёжа)
config = {
    "topology": data,
    "forecasts": "forecasts-mar-09-3.csv",
    "gen_file": "gen-mar-09-3.csv",
    "prices": {
        "h1": 3,
        "h3": 5,
        "h2": 4,
        "h4": 2,
        "s2": 10
    },
    "mode": "predict_money",
    "panel_learn_files": ("gen-mar10-2.csv", "gen-mar10-1.csv", "gen-mar-09-3.csv", "gen-mar-09-2.csv", "gen-mar-09-1.csv", "game-mar08.csv")
}
powerstand = Powerstand(config)
powerstand.run()