import copy


class StationEnergy:
    def __init__(self, upflow=0, downflow=0, losses=0):
        self.upflow = upflow
        self.downflow = downflow
        self.losses = losses

    @property
    def total_energy(self):
        return self.upflow + self.downflow

    def __radd__(self, other):
        self.upflow += other.upflow
        self.downflow += other.downflow
        self.losses += other.losses
        return self

    def __add__(self, other):
        new_st_en = copy.copy(self)
        return new_st_en.__radd__(other)

    def __str__(self):
        return "StationEnergy(upflow={0}, downflow={1}, losses={2})".format(
            self.upflow, self.downflow, self.losses
        )

    def __repr__(self):
        return self.__str__()
