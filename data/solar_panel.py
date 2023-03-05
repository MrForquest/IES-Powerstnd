import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from data.base import Base
from data.utilities import get_column
from main_v2 import config


class SolarPanel(Base):
    def __init__(self, name, connections=None):
        if connections is None:
            connections = list()
        super().__init__(name, connections)
        self.connections = connections
        self.training_files = config["panel_learn_files"]
        self.solar = name

        x = np.array(self.get_column_learn("sun", self.training_files))
        # print(x)
        y = np.array(self.get_column_learn(self.solar, self.training_files))
        # print(y)
        mask = np.where(y <= 0)
        x_fit = np.delete(x, mask)
        y_fit = np.delete(y, mask)
        x_fit = x_fit.reshape(-1, 1)
        self.regr = LinearRegression()
        self.regr.fit(x_fit, y_fit)
        # print(self.regr.predict(np.array(get_column("Солнце: 8", game_file)).reshape(-1, 1)))

    def get_column_learn(self, name, files):
        values = list()
        dfs = list()
        # print(name)
        # print(files)
        for filename in files:
            df = pd.read_csv("forecast/" + filename)
            df = df.fillna(0)
            df[df < 0] = 0
            # print(df[name])
            values.extend(df[name])
        return values

    def set_data(self, data):
        self.data = data

    def get_energy(self, tick):
        if config["mode"] == "predict_money":
            energy = self.regr.predict(np.array([self.data[tick]]).reshape(-1, 1))
            if energy <= 0:
                return 0
            else:
                return energy
        elif config["mode"] == "test_strategy":
            energy = self.data[tick]
            return energy if energy > 0 else 0

    def set_price(self, price):
        self.price = price

    def get_price(self):
        return -self.price

    def __repr__(self):
        return f'SolarPanel("{self.name}")'
