import json

file = open("../logs/game.json", "r")
data = json.load(file)

tick_data = data[0]
# print(tick_data.keys())
# exit()

for tick_data in [data[-1]]:
    # print(tick_data["orders"].get("contents", ""))
    # print(som["class"])
    objs = tick_data["powerstand"]["contents"]["state"]["contents"]["cargo"]["objs"]
    print(tick_data["powerstand"]["contents"]["state"]["contents"]["cargo"]["weatherSun"]["done"])
    for obj in objs:
        if obj["class"] == "wind":
            gen = [p["generated"] for p in obj["power"]["then"]]
            print(obj["address"], gen)  # , obj["score"])  # obj.keys())
    print()
