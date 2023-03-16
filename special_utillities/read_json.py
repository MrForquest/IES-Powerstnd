import json

file = open("../logs/game4.json", "r")
data = json.load(file)

tick_data = data[0]
# print(tick_data.keys())
# exit()

for tick_data in [data[-1]]:
    # print(tick_data["orders"].get("contents", ""))
    # print(som["class"])
    objs = tick_data["powerstand"]["contents"]["state"]["contents"]["cargo"]["objs"]
    print("Ветер")
    print(tick_data["powerstand"]["contents"]["state"]["contents"]["cargo"]["weatherWind"][0][1]["done"])
    for obj in objs:
        if obj["class"] == "wind":
            gen = [p["generated"] for p in obj["power"]["then"]]
            print(*obj["address"])
            print(gen)  # , obj["score"])  # obj.keys())
    print()
