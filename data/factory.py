from data.base import Base
from data.prosumer import Prosumer

from config import config


class Factory(Prosumer):
    def __init__(self, output_obj1, output_obj2=None):
        self.output_obj1 = output_obj1
        self.output_obj2 = output_obj2
        self.output_obj1.set_factory(self)
        if not (output_obj2 is None):
            self.output_obj2.set_factory(self)
        super().__init__("f-AbstractFactory")

    def check2outputs(self):
        net1 = self.output_obj1.connections[0].net
        check1 = net1.online * (not net1.broken)
        check2 = True
        if not (self.output_obj2 is None):
            net2 = self.output_obj2.connections[0].net
            check2 = net2.online * (not net2.broken)

        return check1 and check2

    def get_energy(self, tick):
        if self.check2outputs:
            return -self.data[tick] / 2
        else:
            return -self.data[tick]

    def get_penalty(self, tick):
        net1 = self.output_obj1.connections[0].net
        check1 = net1.online * (not net1.broken)
        check2 = True
        if not (self.output_obj2 is None):
            net2 = self.output_obj2.connections[0].net
            check2 = net2.online * (not net2.broken)

        if check1 or check2:
            return 0
        type_obj = self.name[0]
        penalty_multiplier = config["penalty_mults"][type_obj]
        return -(self.data[tick] * self.price * penalty_multiplier) / 2

    def __repr__(self):
        return f'Factory("{self.output_obj1},{self.output_obj2})")'


class FactoryOutput(Base):
    def __init__(self, name, factory=None, connections=None):
        if connections is None:
            connections = list()
        super().__init__(name, connections)
        self.connections = connections
        self.factory = factory

    def get_energy(self, tick):
        return self.factory.get_energy(tick)

    def get_penalty(self, tick):
        return self.factory.get_penalty(tick)

    def set_factory(self, factory):
        self.factory = factory

    def __repr__(self):
        return f'FactoryOutput("{self.name}")'
