import json

file = open("../logs/final2.json", "r")
data = json.load(file)

tick_data = data[3]
# print(tick_data.keys())

print(tick_data["powerstand"]["contents"]["state"]["contents"]["cargo"]["objs"][0]["contract"])
exit()

for tick_data in [data[-1]]:
    # print(tick_data["orders"].get("contents", ""))
    # print(som["class"])
    objs = tick_data["powerstand"]["contents"]["state"]["contents"]["cargo"]["objs"]
print("Ветер")
print(tick_data["powerstand"]["contents"]["state"]["contents"]["cargo"]["weatherWind"][2][1]["done"])
for obj in objs:
    if obj["class"] == "wind":
        gen = [p["generated"] for p in obj["power"]["then"]]
        print(*obj["address"])
        print(gen)  # , obj["score"])  # obj.keys())
    print()
