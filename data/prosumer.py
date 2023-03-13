from data.base import Base
from config import config


class Prosumer(Base):
    def __init__(self, name, connections=None):
        if connections is None:
            connections = list()
        super().__init__(name, connections)
        self.connections = connections
        self.price = None
        self.data = None

    def set_data(self, data):
        self.data = data

    def get_energy(self, tick):
        return -self.data[tick]

    def set_price(self, price):
        self.price = price

    def get_price(self):
        return self.price

    def get_penalty(self, tick):
        type_obj = self.name[0]
        penalty_multiplier = config["penalty_mults"][type_obj]
        return -self.data[tick] * self.price * penalty_multiplier

    def __repr__(self):
        return f'Prosumer("{self.name}")'
