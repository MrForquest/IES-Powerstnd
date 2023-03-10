from data.base import Base


class Charger(Base):
    def __init__(self, name, connections=None):
        if connections is None:
            connections = list()
        super().__init__(name, connections)
        self.connections = connections
        self.price = None
        self.charger_energy = 0
        self.max_energy = 100
        self.charge_state = False
        self.got_energy = 0

    def charge(self, energy):
        self.got_energy = energy
        self.charge_state = True
        self.got_energy = max(min(energy, 15), 0)
        if self.charger_energy + self.got_energy <= 100:
            self.charger_energy += self.got_energy
        else:
            self.charger_energy = 100
            self.got_energy = self.got_energy + self.charger_energy - 100

    def make_request(self, state, power):
        self.charge_state = state
        self.got_energy = power

    def get_energy(self):
        if self.charge_state:
            self.charge(self.got_energy)
            energy = self.got_energy
            self.got_energy = 0
            return -energy
        elif not self.charge_state:
            self.discharge(self.got_energy)
            energy = self.got_energy
            self.got_energy = 0
            return energy

    def discharge(self, energy):
        self.got_energy = energy
        self.charge_state = False
        self.got_energy = max(min(energy, 15), 0)

        if self.charger_energy - self.got_energy >= 0:
            self.charger_energy -= self.got_energy
        else:
            self.charger_energy = 0
            self.got_energy = self.charger_energy

    def set_price(self, price):
        self.price = price

    def get_price(self):
        return self.price

    def __repr__(self):
        return f'Charger("{self.name}")'
