from data.base import Base


class Prosumer(Base):
    def __init__(self, name, connections=None):
        if connections is None:
            connections = list()
        super().__init__(name, connections)
        self.connections = connections

    def get_energy(self):
        return 0

    def __repr__(self):
        return f'Prosumer("{self.name}")'
