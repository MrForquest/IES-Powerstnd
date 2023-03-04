from sklearn.linear_model import LinearRegression
import numpy as np


class WES:
    def __init__(self, name, n_values=3):
        self.name = name
        self.model = LinearRegression()
        self.n_values = n_values

    def preprocess_data(self, data):
        wind_array_ = data
        wind_array_ = wind_array_**3
        wind_data_ = list()
        for i in range(self.n_values):
            wind_last_ = np.roll(wind_array_, i)
            wind_last_[0 : (i + 1)] = 0
            wind_data_.append(wind_last_)
        new_wind_ = list()
        for i in range(len(wind_array_)):
            new_wind_.append(tuple(wind_data_[j][i] for j in range(self.n_values)))
        return new_wind_

    def train(self, data):
        train_x_processed = self.preprocess_data(data["wind"])
        y_train = data[self.name]
        self.model.fit(train_x_processed, y_train)

    def predict(self, tick, data):
        wind_processed = [self.preprocess_data(data["wind"])[tick]]
        energy = self.model.predict(wind_processed)
        energy = np.maximum(energy, 0)
        energy = np.minimum(energy, 15)
        return energy

    def predict_many(self, tick_start, tick_end, data):
        wind_processed = self.preprocess_data(data["wind"])[tick_start:tick_end]
        energy = self.model.predict(wind_processed)
        energy = np.maximum(energy, 0)
        energy = np.minimum(energy, 15)
        return energy
