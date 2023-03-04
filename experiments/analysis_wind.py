import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from wes import WES
from sklearn.metrics import mean_squared_error

names = [
    "gen-final-1.csv",
    "gen-final-n1.csv",
    "gen-mar11-2.csv",
    "gen-mar10-4.csv",
    "gen-mar10-2.csv",
    "gen-mar10-1.csv",
    "gen-mar-09-3.csv",
    "gen-mar-09-2.csv",
    "gen-mar-09-1.csv",
    "game-mar08.csv",
]
path = "../forecast/"
train_names, test_names = names[4:], names[:4]

data = pd.DataFrame()

for filename in names:
    df = pd.read_csv(path + filename)
    df["filename"] = filename
    data = pd.concat([data, df], axis=0)

data_group = data.groupby(["filename"])
data_dict = dict()
for line in data_group:
    line[1].sort_values("tick")
    data_dict[line[0]] = line[1]

group_name = "game-mar08.csv"
# data[name] = data[name].fillna(0)
# data[name].describe()
curr_data = data_dict[group_name]

print("start_train")
errors = list()
for flnd in data_dict.keys():
    wind_station = WES("a5")
    wind_station.train(curr_data)
    mean_error = mean_squared_error(
        data_dict[flnd]["a5"], wind_station.predict_many(0, 101, data_dict[flnd])
    )
    errors.append(mean_error)
    print(flnd, mean_error)
print(sum(errors) / len(errors))
print(max(errors), min(errors))
print(sorted(errors))

# for i in range(101):
#    print(wind_station.predict(i, curr_data))
# print(curr_data["a8"][50])
