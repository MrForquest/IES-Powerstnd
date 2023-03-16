import json

file = open("../logs/game.json", "r")
data = json.load(file)

tick_data = data[2]

forecasts = tick_data["powerstand"]["contents"]["state"]["contents"]["cargo"]["forecasts"]

# for obj in objs:
#    print(obj["class"], obj["id"], obj["power"]["now"], obj["score"])  # obj.keys())
print(forecasts["sfClass3A"]["forecast"]["values"])
