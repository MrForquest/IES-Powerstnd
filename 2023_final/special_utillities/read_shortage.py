import json
import re

file = open("../logs/final1.json", "r")
data = json.load(file)

tick_data = data[10]
# print(tick_data["processes"][0]["stdout"])
# exit()

for i, tick_data in enumerate(data[:100]):
    # print(tick_data["processes"][0].keys())
    # print(tick_data["orders"])
    # print(som["class"])
    power = tick_data["powerstand"]["contents"]["state"]["contents"]["cargo"]["totalPowers"][0][1]["now"]
    print(i)
    # print(power["hypotheticallyGenerated"])
    # , 'totalConsumed', 'totalFromExternal', 'totalGenerated', 'totalLost']
    # print(power["generatedSolar"])
    print(power["totalGenerated"] - power["totalConsumed"] - power["totalLost"])
    stdout = tick_data["processes"][0]["stdout"]
    match = re.search(r"(SHORT( | -)\d+\.\d+)", stdout)
    if match:
        my_short = float(match.groups()[0].replace("SHORT ", ""))
        print(my_short)
    print()
