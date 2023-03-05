import random

from data.line import Line
from data.prosumer import Prosumer
from data.station import Station
from data.station_energy import StationEnergy
from data.utilities import get_energy_loss


class Powerstand:
    def __init__(self, config):
        self.config = config
        topology = self.config["topology"]

        names = list()
        for d in topology:
            names.extend((d["station"], d["address"]))
        self.all_names = list(set(names))
        self.st_names = list(set([na for na in names if na[0] in ("m", "e", "M")]))
        self.prosumer_names = list(set([na for na in names if na[0] not in ("m", "e")]))
        self.all_stations = []
        self.prosumers = [
            Prosumer(na) for na in self.prosumer_names if na[0] not in ("m", "e")
        ]
        self.all_stations = [Station(stn) for stn in self.st_names]
        self.objects = {obj.name: obj for obj in (self.prosumers + self.all_stations)}
        self.main_st = filter(
            lambda stn_: stn_.name == "M1", self.all_stations
        ).__next__()
        self.all_lines = list()

        line_names = list(
            set([" ".join((line["station"], str(line["line"]))) for line in topology])
        )
        for line_name in line_names:
            st_name, line_id = line_name.split()
            line_id = int(line_id)
            lines = filter(
                lambda li: li["station"] == st_name and li["line"] == line_id, topology
            )
            station = self.get_object(st_name)
            line_obj = Line(station, line_id=line_id)
            for line in lines:
                address = self.get_object(line["address"])
                line_obj.append_address(address)
                address.append_connection(line_obj)
            station.append_line(line_obj)
            self.all_lines.append(line_obj)

        self.init_objects()

    def init_objects(self):
        pass

    def get_object(self, name):
        return self.objects[name]

    def tree_traversal_rec(self, station):
        st_energy = StationEnergy(0, 0, 0)

        networks = station.get_networks()
        for net in networks:
            if net.broken:
                net.decrement_cooldown()
                # todo штрафы
            if not net.online:
                net.upflow, net.downflow, net.losses = 0, 0, 0
                # todo штрафы
                continue
            addresses = net.line.get_address()
            print(addresses)
            if isinstance(addresses[0], Station):
                subordinate_st_energy = self.tree_traversal_rec(addresses[0])
                st_energy += subordinate_st_energy
            else:
                line_energy = 0
                for addr in addresses:
                    line_energy += addr.get_energy(tick)

                if line_energy > 0:
                    st_energy.upflow += line_energy
                elif line_energy < 0:
                    st_energy.downflow += line_energy
                st_energy.losses += get_energy_loss(line_energy)

            net.calc_wear(st_energy.total_energy)
            chance = random.random()
            if net.prob_broken() < chance:
                net.broken = True
                net.break_net()
        return st_energy

    def run(self):
        print(self.all_lines)
        energy = self.tree_traversal_rec(self.main_st)
        print(energy)


# Серёжа хочет видеть такие МЕТОДЫ у соотвующих объектов(SolarPanel, SmallHouse и другие)
class SomeObject:
    def set_data(self, data):
        ...

    def get_energy(self, tick):
        ...
