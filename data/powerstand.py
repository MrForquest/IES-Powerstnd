import random
from random import randint
from argparse import Namespace

from data.line import Line
from data.prosumer import Prosumer
from data.station import Station
from data.station_energy import StationEnergy
from data.utilities import get_energy_loss, get_column
from data.small_house import SmallHouse
from data.solar_panel import SolarPanel
from data.factory import Factory, FactoryOutput
from data.hospital import Hospital, HospitalOutput
from data.charger import Charger


class Powerstand:
    def __init__(self, config):
        self.config = config
        topology = self.config["topology"]

        names = list()
        self.total_money = 0
        self.tick = 0
        for d in topology:
            names.extend((d["station"], d["address"]))

        # имена объектов
        self.all_names = list(set(names))
        self.st_names = list(set([na for na in names if na[0] in ("M", "m", "e")]))
        self.prosumer_names = list(
            set([na for na in names if na[0] not in ("M", "m", "e", "s", "a")])
        )

        # солнечные панели
        self.panels = [SolarPanel(na) for na in self.prosumer_names if na[0] in "s"]

        # заводы
        factories_names = [na for na in self.prosumer_names if na[0] in "f"]
        self.factories = list()
        self.factories_outputs = [FactoryOutput(na) for na in factories_names]
        # self.small_houses = [SolarPanel(na) for na in self.prosumer_names if na[0] in "s"]

        # больницы
        hospital_names = [na for na in self.prosumer_names if na[0] in "b"]
        self.hospitals = list()
        self.hospitals_outputs = [FactoryOutput(na) for na in factories_names]

        # дома потребители
        self.prosumers = [
            Prosumer(na)
            for na in self.prosumer_names
            if na[0] not in ("M", "m", "e", "s", "a", "f")
        ]

        # аккумуляторы
        self.charger_names = [na for na in self.prosumer_names if na[0] in "c"]
        self.chargers = [Charger(na) for na in self.charger_names]

        # станциии
        self.all_stations = list()
        self.all_stations = [Station(stn) for stn in self.st_names]
        self.main_st = filter(
            lambda stn_: stn_.name[0] == "M", self.all_stations
        ).__next__()

        self.objects_n2obj = {
            obj.name: obj
            for obj in (
                    self.prosumers
                    + self.panels
                    + self.all_stations
                    + self.factories_outputs
            )
        }
        # линии
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

        # инициализация объектов Заводов
        numbers_str = "123456789ABCDEF"
        numbers_dict = dict(zip(list(numbers_str), range(len(numbers_str))))
        factories_names.sort()
        for i, f_na in enumerate(factories_names):
            ind = numbers_dict[f_na[1]]
            if ind % 2 == 0:
                if i != len(factories_names) - 1:
                    f_na_2 = factories_names[i + 1]
                    ind_2 = numbers_dict[f_na_2[1]]
                    fo2 = None
                    if ind_2 - ind == 1:
                        fo1 = self.get_object(f_na)
                        fo2 = self.get_object(f_na_2)
                    else:
                        fo1 = self.get_object(f_na)
                    new_factory = Factory(fo1, fo2)
                    self.factories.append(new_factory)

        # инициализация объектов Больниц
        hospital_names.sort()
        for i, f_na in enumerate(hospital_names):
            ind = numbers_dict[f_na[1]]
            if ind % 2 == 0:
                if i != len(hospital_names) - 1:
                    f_na_2 = hospital_names[i + 1]
                    ind_2 = numbers_dict[f_na_2[1]]
                    fo2 = None
                    if ind_2 - ind == 1:
                        fo1 = self.get_object(f_na)
                        fo2 = self.get_object(f_na_2)
                    else:
                        fo1 = self.get_object(f_na)
                    new_hospital = Hospital(fo1, fo2)
                    self.hospitals.append(new_hospital)

        print(self.factories)
        self.objects = (
                self.factories
                + self.hospitals
                + self.all_lines
                + self.panels
                + self.prosumers
                + self.all_names
                + self.chargers
        )
        self.init_objects()

    def init_orders(self):
        self.orders = Namespace(
            charge=lambda address, power: self.__change_cell(address, power, True),
            discharge=lambda address, power: self.__change_cell(address, power, False),
            line_on=lambda address, line: self.set_line(address, line, True),
            line_off=lambda address, line: self.set_line(address, line, False),
        )

    def init_objects(self):
        forecast_num = 2  # randint(1, 9)
        for obj in self.objects_n2obj.values():
            if obj.name[0] in "h":
                obj.set_data(
                    get_column(f"""Дома А: {forecast_num}""", self.config["forecasts"])
                )
            elif obj.name[0] in "d":
                obj.set_data(
                    get_column(f"""Дома Б: {forecast_num}""", self.config["forecasts"])
                )
            elif obj.name[0] in "f":
                print(obj)
                obj.factory.set_data(
                    get_column(f"""Заводы: {forecast_num}""", self.config["forecasts"])
                )
            elif obj.name[0] in "b":
                obj.set_data(
                    get_column(
                        f"""Больницы: {forecast_num}""", self.config["forecasts"]
                    )
                )
            elif obj.name[0] in "s":
                obj.set_data(get_column(obj.name, self.config["gen_file"]))
        for name in self.config["prices"]:
            obj = self.objects_n2obj[name]
            if isinstance(obj, FactoryOutput):
                obj.factory.set_price(self.config["prices"][name])
            else:
                obj.set_price(self.config["prices"][name])

    def get_object(self, name):
        return self.objects_n2obj[name]

    def tree_traversal_rec(self, station):
        st_energy = StationEnergy(0, 0, 0)

        networks = station.get_networks()
        for net in networks:
            addresses = net.line.get_address()

            if net.broken:
                net.upflow, net.downflow, net.losses = 0, 0, 0
                net.decrement_cooldown()
            if not net.online:
                net.upflow, net.downflow, net.losses = 0, 0, 0

            station.now_available *= net.online * (not net.broken)
            print(addresses)
            line_energy = 0
            if isinstance(addresses[0], Station):
                addresses[0].now_available *= station.now_available
                subordinate_st_energy = self.tree_traversal_rec(addresses[0])
                st_energy += subordinate_st_energy
            else:
                for addr in addresses:
                    energy = addr.get_energy(self.tick)
                    if station.now_available:
                        line_energy += energy
                        if isinstance(addr, FactoryOutput):
                            self.total_money += addr.factory.get_price() * energy
                        else:
                            self.total_money += addr.get_price() * energy
                    else:
                        print("aaaa", addr.get_penalty(self.tick))
                        self.total_money += addr.get_penalty(self.tick)

                if line_energy > 0:
                    st_energy.upflow += line_energy
                elif line_energy < 0:
                    st_energy.downflow += line_energy
                st_energy.losses += get_energy_loss(line_energy)

            if line_energy != 0:
                net.calc_wear(line_energy)
                chance = random.random()
                if net.prob_broken() > chance:
                    net.broken = True
                    net.break_net()

        return st_energy

    def clean_all_stations(self):
        for st in self.all_stations:
            st.now_available = True

    def set_line(self, address, line, val):
        if not (address in self.st_names):
            raise ValueError(f"Нет такой станции {address}")
        station = self.get_object(address)
        line_obj = station.get_line(line)
        if not (address in self.st_names):
            raise ValueError(f"Нет такой станции {address}")
        order_type = "lineOn" if val else "lineOff"
        order = {"orderT": order_type, "line": {"id": line, "line": line_obj}, "address": address}
        self.__order.append(order)

    def __change_cell(self, name, energy, charge=True):
        order = "charge" if charge else "discharge"
        if energy < 0:
            raise ValueError('Неправильное значение добавляемой энергии. Приказ не принят')
        elif name not in self.objects:
            raise NameError("Такого накопителя нет в топологии. Приказ не принят")
        else:
            self.__orders.append({"orderT": order, "name": name, "power": energy})

    def __charge(self, name, energy):
        self.objects_n2obj[name].charge(energy)

    def __discharge(self, name, energy):
        self.objects_n2obj[name].discharge(energy)

    def __set_line(self, station_name, line_id, val):
        station = self.objects_n2obj[station_name]

        if not isinstance(station, Station):
            raise TypeError(f"{station} не станция!")

        line = station.get_line(line_id)
        net = line.net
        net.online = val

    def run(self):
        for i in range(100):
            self.tick = i
            self.clean_all_stations()
            energy = self.tree_traversal_rec(self.main_st)
            if energy.total_energy < 0:
                self.total_money -= energy.total_energy * (-10)
            elif energy.total_energy > 0:
                self.total_money += energy.total_energy * 1
            print(f"""energy for tick {self.tick}: {energy}""")
            print(f"""total money for tick {self.tick}: {self.total_money}""")
        print(self.factories[0])
        print(sum(self.factories[0].data))


# Серёжа хочет видеть такие МЕТОДЫ у соотвующих объектов(SolarPanel, SmallHouse и другие)
class SomeObject:
    def set_data(self, data):
        ...

    def get_energy(self, tick):
        ...
