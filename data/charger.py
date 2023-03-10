from data.base import Base


class Charger(Base):
    def __init__(self, name, connections=None):
        if connections is None:
            connections = list()
        super().__init__(name, connections)
        self.connections = connections
        self.price = None
        self.energy = 0
        self.max_energy = 100

    def charge(self, energy):
        energy = max(min(energy, 15), 0)
        if self.energy + energy <= 100:
            self.energy += energy
        else:
            self.energy = 100

    def discharge(self, energy):
        energy = max(min(energy, 15), 0)
        if self.energy - energy >= 0:
            self.energy -= energy
        else:
            self.energy = 0

    def set_price(self, price):
        self.price = price

    def get_price(self):
        return self.price

    def __repr__(self):
        return f'Charger("{self.name}")'
