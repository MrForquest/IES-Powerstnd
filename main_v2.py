import json
import random
from data.powerstand import Powerstand
from config import config

"""
data = [
    {"address": "h1", "station": "M1", "line": 1},
    {"address": "s2", "station": "M1", "line": 2},
    {"address": "m2", "station": "M1", "line": 3},
    {"address": "h2", "station": "m2", "line": 1},
    {"address": "h3", "station": "m2", "line": 2},
    {"address": "h4", "station": "m2", "line": 2},
]

"""

# mode - "predict_money"(Дима)/"test_strategy"(Серёжа)
random.seed(2)
powerstand = Powerstand(config)
powerstand.run()
