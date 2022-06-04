from data.line import Line
from data.prosumer import Prosumer
from data.station import Station
from data.utilities import get_energy_loss


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
