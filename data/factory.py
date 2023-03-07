from data.base import Base


class Factory:
    def __init__(self, line_obj1, line_obj2=None):
        self.line_obj1 = line_obj1
        self.line_obj2 = line_obj2

    def set_data(self, data):
        self.data = data

    def get_energy(self, tick):
        if self.line_obj1 and self.line_obj2:
            return -self.data[tick] / 2
        else:
            return -self.data[tick]

    def set_price(self, price):
        self.price = price

    def get_price(self):
        return self.price


class FactoryOutput(Base):
    def __init__(self, name, factory=None, connections=None):
        if connections is None:
            connections = list()
        super().__init__(name, connections)
        self.connections = connections
        self.factory = factory

    def get_energy(self, tick):
        return self.factory.get_energy(tick)

    def set_factory(self, factory):
        self.factory = factory

    def __repr__(self):
        return f'FactoryOutput("{self.name}")'
