import json
from typing import List

data = [{"address": "h1", "station": "M1", "line": 1},
        {"address": "t1", "station": "M1", "line": 2},
        {"address": "m2", "station": "M1", "line": 3},
        {"address": "h2", "station": "m2", "line": 1},
        {"address": "h3", "station": "m2", "line": 2},
        {"address": "h4", "station": "m2", "line": 2}]


class Line:
    def __init__(self, station, line_id, address=None):
        if address is None:
            address = list()
        self.station = station
        self.address = address
        self.line_id = line_id

    def append_address(self, address):
        self.address.append(address)

    def get_station(self):
        return self.station

    def get_address(self):
        return self.address

    def get_line_id(self):
        return self.line_id

    def __repr__(self):
        return f"Line{self.line_id} {self.station} to {self.address}"


class Base:
    def __init__(self, name, connections):
        self.name = name
        self.connections = connections

    def append_connection(self, line: Line):
        self.connections.append(line)


class Prosumer(Base):
    def __init__(self, name, connections=None):
        if connections is None:
            connections = list()
        super().__init__(name, connections)
        self.connections = connections

    def get_energy(self):
        return 0

    def __repr__(self):
        return f"Prosumer(\"{self.name}\")"


class Station(Base):
    def __init__(self, name, connections=None, lines_=None):
        if connections is None:
            connections = list()
        if lines_ is None:
            lines_ = list()
        super().__init__(name, connections)
        self.lines = lines_

    def set_lines(self, lines: List[Line]):
        self.lines = lines

    def get_lines(self):
        return self.lines

    def append_line(self, line: Line):
        self.lines.append(line)

    def __repr__(self):
        return f"Station(\"{self.name}\")"


def get_energy_loss(energy):
    return energy * 0.1


class Powerstand:
    def __init__(self, topology, game_info=None):
        names = list()
        for d in topology:
            names.extend((d["station"], d["address"]))
        self.all_names = list(set(names))
        self.st_names = list(set([na for na in names if na[0] in ("m", "e", "M")]))
        self.prosumer_names = list(set([na for na in names if na[0] not in ("m", "e")]))
        self.all_stations = []
        self.prosumers = [Prosumer(na) for na in self.prosumer_names if na[0] not in ("m", "e")]
        self.all_stations = [Station(stn) for stn in self.st_names]
        self.objects = {obj.name: obj for obj in (self.prosumers + self.all_stations)}
        self.main_st = filter(lambda stn_: stn_.name == "M1", self.all_stations).__next__()
        self.all_lines = list()
        line_names = list(set([" ".join((line["station"], str(line["line"]))) for line in topology]))
        for line_name in line_names:
            st_name, line_id = line_name.split()
            line_id = int(line_id)
            lines = filter(lambda li: li["station"] == st_name and li["line"] == line_id, topology)
            station = self.get_object(st_name)
            line_obj = Line(station, line_id=line_id)
            for line in lines:
                address = self.get_object(line["address"])
                line_obj.append_address(address)
                address.append_connection(line_obj)
            station.append_line(line_obj)
            self.all_lines.append(line_obj)

    def get_object(self, name):
        return self.objects[name]

    def tree_traversal_rec(self, station):
        sum_energy = 0
        for line in station.get_lines():
            address = line.get_address()
            print(address)
            if issubclass(address[0].__class__, Station):
                sum_energy += self.tree_traversal_rec(address[0])
            else:
                line_energy = 0
                for addr in address:
                    line_energy += addr.get_energy()
                line_energy -= get_energy_loss(line_energy)
                sum_energy += line_energy
        return sum_energy

    def run(self):
        print(self.all_lines)
        self.tree_traversal_rec(self.main_st)


powerstand = Powerstand(data)
powerstand.run()
