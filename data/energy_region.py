import math
from data.utilities import get_wear


class EnergyRegion:
    nominal_energy = 30

    def __init__(self, line):
        self.wear = 0
        self.online = False
        self.upflow = 0
        self.downflow = 0
        self.losses = 0
        self.broken = False
        self.line = line
        self.line.net = self
        self.max_cooldown = 5
        self.cooldown = 0

    def net_off(self):
        self.online = False

    def net_on(self):
        self.online = True

    def calc_wear(self, energy):
        # x = abs(energy) / self.nominal_energy
        # w = pow(x, 1.9) / 6
        w = get_wear(abs(energy))
        self.wear += w

    def prob_broken(self):
        return 0
        divider = pow(math.e, 36 - 40 * self.wear) + 1
        p = 1 / divider
        return p

    def break_net(self):
        self.cooldown = self.max_cooldown
        self.wear = 0

    def decrement_cooldown(self):
        if self.cooldown:
            self.cooldown -= 1
        else:
            self.broken = False

    def location(self):
        return self.line.station.id, self.line.line_id

    def __repr__(self):
        return f"Net: {self.location()}"
