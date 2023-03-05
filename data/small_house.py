import copy
from data.base import Base
from data.utilities import get_column


class SmallHouse(Base):
    def __init__(self, name, connections=None):
        if connections is None:
            connections = list()
        super().__init__(name, connections)
        self.connections = connections

    def set_data(self, data):
        self.data = data

    def get_energy(self, tick):
        return get_column("Дома А: 1", self.data)[tick]

    def set_price(self, price):
        self.price = price

    def get_price(self):
        return self.price

    def __repr__(self):
        return f'SmallHouse("{self.name}")'
