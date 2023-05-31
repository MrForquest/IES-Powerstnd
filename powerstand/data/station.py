from powerstand.data.base import Base
from powerstand.data.line import Line
from powerstand.data.energy_region import EnergyRegion
from typing import List


class Station(Base):
    def __init__(self, name, connections=None, lines_=None):
        if connections is None:
            connections = list()
        if lines_ is None:
            lines_ = list()
        super().__init__(name, connections)
        self.lines = lines_
        self.networks = list()
        self.id = name
        self.now_available = True
        self.update_networks()

    def get_networks(self):
        return self.networks

    def update_networks(self):
        self.networks = [EnergyRegion(line) for line in self.lines]

    def set_lines(self, lines: List[Line]):
        self.lines = lines
        self.update_networks()

    def get_lines(self):
        return self.lines

    def get_line(self, line_id):
        for line in self.lines:
            if line.line_id == line_id:
                return line
        else:
            raise ValueError(f"У станции {self} нет линии c id {line_id}")

    def append_line(self, line: Line):
        self.lines.append(line)
        self.update_networks()

    def __repr__(self):
        return f'Station("{self.name}")'
