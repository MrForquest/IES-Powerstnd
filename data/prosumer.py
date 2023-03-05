from data.base import Base


class Prosumer(Base):
    def __init__(self, name, connections=None):
        if connections is None:
            connections = list()
        super().__init__(name, connections)
        self.connections = connections

    def set_data(self, data):
        self.data = data

    def get_energy(self, tick):
        return -self.data[tick]

    def set_price(self, price):
        self.price = price

    def get_price(self):
        return self.price

    def __repr__(self):
        return f'Prosumer("{self.name}")'
