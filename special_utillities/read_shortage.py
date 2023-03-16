import json
import re

file = open("../logs/game.json", "r")
data = json.load(file)

tick_data = data[10]
# print(tick_data["processes"][0]["stdout"])
# exit()

for tick_data in data:
    # print(tick_data["processes"][0].keys())
    print(tick_data["orders"])
    # print(som["class"])

    # stdout = tick_data["processes"][0]["stdout"]
    # matches = re.search(r"SHORT( | -)\d+\.\d+", stdout)

    # print(matches)
