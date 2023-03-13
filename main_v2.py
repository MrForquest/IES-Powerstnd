import json
import random
from data.powerstand import Powerstand
from data.station import Station
from config import config

"""
data = [
    {"address": "h1", "station": "M1", "line": 1},
    {"address": "s2", "station": "M1", "line": 2},
    {"address": "m2", "station": "M1", "line": 3},
    {"address": "h2", "station": "m2", "line": 1},
    {"address": "h3", "station": "m2", "line": 2},
    {"address": "h4", "staton": "m2", "line": 2},
]

"""


def user_script(psm: Powerstand):
    for obj in psm.objects:
        print("types")
        print(obj.type)
        print("-" * 20)

        if obj.type in ("miniA", "miniB"):
            for line in obj.get_lines():
                psm.orders.line_on(obj.name, line.line_id)

    psm.orders.charge('c3', 100)
    psm.save_and_exit()


# mode - "predict_money"(Дима)/"test_strategy"(Серёжа)
random.seed(2)
powerstand = Powerstand(config)
powerstand.set_user_script(user_script)
powerstand.run(10)
