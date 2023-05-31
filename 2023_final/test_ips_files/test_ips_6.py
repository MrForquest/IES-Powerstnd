import ips
import numpy as np
from string import ascii_uppercase, digits

sec_num = digits + ascii_uppercase

# Износ линии, при котором линия отключается
CRITICAL_WEAR = 0.5
# линии с этими объектами не отключаются при высоком износе( у них внутряняя логика )
IGNORE_GLOBAL_LINE_OFF = ["s6", "sB"]
# линии с этими объектами будут отключены в любом случае
MUST_GLOBAL_LINE_OFF = ["", ""]
# экстренная зарядка акб на ...мВ
EMERGENCE_charge_acbs = 15
# экстренная разрядка акб на ...мВ
EMERGENCE_DIScharge_acbs = 0
# После кого тика будет постоянная разрядка АКБ
TICK_ENERGY_OUT = 50
# После кого тика будет постоянная разрядка АКБ
DISCHARGE_END_ENERGY = 5


class Station:
    def __init__(self, st_obj):
        self.address = st_obj.address
        self.s_obj = st_obj
        self.connections = list()


class MyController:
    def __init__(self, psm):
        self.psm = psm
        self.accums = ["c1"]
        self.prices = {"hA": 8, "h6": 5, "hI": 5}
        self.table = "В"

        self.obj_types = [
            "main"  # подстанции
            "miniA",  # мини-подстанции А
            "miniB",  # мини-подстанции Б
            "solar",  # солнечные электростанции
            "wind",  # ветровые электростанции
            "houseA",  # дом А
            "houseB",  # дом Б
            "factory",  # больницы
            "hospital",  # заводы
            "storage",  # накопители
        ]

        self.id2obj = dict()
        for obj in self.psm.objects:
            self.id2obj[obj.id] = obj

        self.station_names = {"main", "miniA", "miniB"}

        self.addr2obj = {obj.address[0]: obj for obj in self.psm.objects}

        self.past_tick = max(psm.tick - 1, 0)
        self.next_tick = min(psm.tick + 1, len(psm.forecasts.houseA) - 1)
        # tables ['S1c16', 'S1c15', 'S1a3', 'S1c17', 'S1c14', 'S1c13', 'S1c11']
        self.now_wind = max(psm.forecasts.wind[self.table][self.psm.tick], 0)
        self.next_wind = max(psm.forecasts.wind[self.table][self.next_tick], 0)
        self.past_sun = max(psm.forecasts.sun[self.past_tick], 0)
        self.now_sun = max(psm.forecasts.sun[self.psm.tick], 0)
        self.next_sun = max(psm.forecasts.sun[self.next_tick], 0)

        # пока не используются
        self.consumption = 0  # прогноз суммарного потребления
        self.generation = 0  # прогноз суммарной генерации

    def sun_formule(self, x, y):
        # print(x, ",", y)
        gen = np.array(x)
        sun = np.array(y)

        sun[sun < 0] = 0
        gen[sun < 0] = 0
        gen[gen < 0.1] = 0
        sun[gen < 0.1] = 0

        sun = sun[gen > 0.1]
        gen = gen[gen > 0.1]

        f0 = np.array([1] * len(gen))

        Y = sun.reshape(-1, 1)
        w = np.array([np.nan, np.nan])
        X = np.array([f0, gen]).T
        coef_matrix = np.dot(np.dot(np.linalg.inv(np.dot(X.T, X)), X.T), Y)

        b = coef_matrix.T[0][0]
        coef = coef_matrix.T[0][1]

        # рассчитаем коэффициенты используя формулу
        return coef, b

    def get_obj_st(self, obj):
        line_obj = obj.path[0][-1]
        obj_st = self.id2obj[line_obj.id].address[0]
        line_num = line_obj.line
        return obj_st, line_num

    def print_obj(self, obj):
        print("== Объект:", obj.id, "==")  # (тип, номер)
        print("Тип: ", obj.type)  # см. выше
        print("Включен:", obj.power.now.online)  # bool
        print("Тариф:", obj.contract)  # float
        print("Адрес:", obj.address)  # [str]
        print("Энергорайоны:",
              obj.path)  # [адрес энергорайона]
        print("Доход:",
              obj.score.now.income)  # float
        print("Расход:",
              obj.score.now.loss)  # float
        print("Генерация:",
              obj.power.now.generated)  # float
        print("Потребление:",
              obj.power.now.consumed)  # float
        print("Заряд (актуально для накопителя):",
              obj.charge.now)  # float

    def print_net(self, index, net):
        print("== Энергорайон", index, "==")
        print("Адрес:", net.location)
        # (ID подстанции, № линии)]
        print("Включен:", net.online)  # bool
        print("Генерация:", net.upflow)  # float
        print("Потребление:", net.downflow)  # float
        print("Потери:", net.losses)  # float
        print("Износ ветки:", net.wear)  # float

    def print_public_info(self):
        print("Ход:", self.psm.tick)  # int
        print("Всего ходов:", self.psm.gameLength)  # int
        print("Изменение счёта:", self.psm.scoreDelta)  # float
        print("Всего сгенерировано:",
              self.psm.total_power.generated)  # float
        print("Всего потреблено:",
              self.psm.total_power.consumed)  # float
        print("Получено с биржи (минус = отправлено):",
              self.psm.total_power.external)  # float
        print("Всего потерь:",
              self.psm.total_power.losses)  # float
        print("-" * 20)
        print("конец")

    def all_lines_on(self):
        for obj in self.psm.objects:
            addr = obj.address[0]
            if obj.type in self.station_names:
                # включаем линии
                for i in range(2 if obj.type == "miniB" else 3):
                    self.psm.orders.line_on(addr, i + 1)

    def objects_process(self):
        generation = 0
        consumption = 0
        for obj in self.psm.objects:
            addr = obj.address[0]
            if obj.path != (tuple(),):
                line_obj = obj.path[0][-1]
                obj_st = self.id2obj[line_obj.id].address[0]
                line_num = line_obj.line
            else:
                obj_st = None
                line_num = None

            if obj.type == "wind":
                generation += self.wind_process(obj)
                continue
            if obj.type == "solar":
                # вычисляем прогноз солнца
                generation += self.solar_process(obj)
                continue

            # вычисляем прогноз потребления
            if obj.type.lower() == "housea":
                additional = 0.82 * (5 - self.prices[addr]) ** 2.6 if self.prices[addr] < 5 else 0
                consumption += psm.forecasts.houseA[self.next_tick] + additional + 0.5
            if obj.type.lower() == "houseb":
                additional = 0.24 * (9 - self.prices[addr]) ** 2.2 if self.prices[addr] < 8 else 0
                consumption += psm.forecasts.houseB[self.next_tick] + additional + 0.5
            if obj.type == "factory":
                consumption += psm.forecasts.factory[self.next_tick] + 0.5
            if obj.type == "hospital":
                consumption += psm.forecasts.hospital[self.next_tick] + 0.5

        shortage = abs(generation) - abs(consumption) - (
                consumption / psm.total_power.consumed) * psm.total_power.losses
        return shortage

    def wind_process(self, obj):
        # вычисляем прогноз ветра
        obj_st, line_num = self.get_obj_st(obj)
        loc2net = {net.location: net for net in self.psm.networks.values()}
        wind_net = loc2net[obj.path[0]]
        if not wind_net.online:
            self.psm.orders.line_on(obj_st, line_num)
            return 0
        if obj.failed:
            self.psm.orders.line_off(obj_st, line_num)
            return 0
        else:
            if self.now_wind <= self.next_wind:
                return obj.power.now.generated * 1.10
            else:  # now_wind > next_wind
                return obj.power.now.generated * 0.85

    def solar_process(self, obj):
        """
        Обработка солнечных панелей
        """
        obj_st, line_num = self.get_obj_st(obj)
        # print("Реальность предыдущего:", obj.power.now.generated)
        corr_next_sun = max(0, self.next_sun - 0.5)
        zero_bold = 0.05
        # отключение линий с панелями ночью для починки
        if (obj.power.then[self.past_tick].generated >= zero_bold) and (obj.power.now.generated <= zero_bold):
            self.psm.orders.line_off(obj_st, line_num)
            return 0

        # self.id2obj[obj.path[0][-1].id].address
        energy = 0
        if psm.tick >= 50:
            obj_gens = [line.generated for line in obj.power.then]
            coef_, b_ = self.sun_formule(psm.sun.then, obj_gens)
            energy = self.next_sun * coef_ + b_
            # print("Параметры панели", coef_, b_)
            energy = max(min(25, energy), 0)
        else:
            if self.now_sun == 0:
                energy = 0
            else:
                energy = obj.power.now.generated * (corr_next_sun / self.now_sun)

        return energy

    def charge_acbs(self, energy):
        d_eng = max(min((energy / len(self.accums)), 15), 0)
        for acb in self.accums:
            self.psm.orders.charge(acb, d_eng)

    def discharge_acbs(self, energy):
        d_eng = max(min((energy / len(self.accums)), 15), 0)
        for acb in self.accums:
            psm.orders.discharge(acb, d_eng)

        self.psm.orders.humanize()

    def calc_acb(self, shortage, acb_charge, f=False):
        if (100 - acb_charge) >= 15:
            if shortage < 15:
                if f:
                    self.charge_acbs(shortage)
                return 0
            else:
                if f:
                    self.charge_acbs(15)
                return shortage - 15
        else:
            if shortage < (100 - acb_charge):
                if f:
                    self.charge_acbs(shortage)
                return 0
            else:
                if f:
                    self.charge_acbs(100 - acb_charge)
                return shortage - (100 - acb_charge)

    def calc_shortage(self, next_shortage, next_next_shortage, next_acb_charge):
        if next_shortage > 0:
            new_shortage = self.calc_acb(next_shortage, self.charger_obj.charge, f=True)
        if next_shortage < 0:
            self.discharge_acbs(abs(next_shortage))

        if next_next_shortage > 0:
            new_new_shortage = self.calc_acb(next_next_shortage, next_acb_charge)
            self.psm.orders.sell(new_new_shortage, 10)

    def get_full_acb_charge(self):
        all_charge = 0
        for addr_acb in self.accums:
            acb_obj = self.addr2obj[addr_acb]
            all_charge += acb_obj.charge.now
        return all_charge

    def close(self):
        self.psm.save_and_exit()

    def run(self):
        global Emergence_charge_acbs
        global Emergence_DIScharge_acbs
        global CRITICAL_WEAR

        print("Тик", self.psm.tick)
        self.all_lines_on()
        shortage = self.objects_process()
        print("SHORT", shortage)

        if shortage > 0:
            if self.get_full_acb_charge() >= 99.9 * len(self.accums):
                self.psm.orders.sell(abs(shortage) * 0.7, 10)
            else:
                self.charge_acbs(abs(shortage) * 0.9)
        elif shortage < 0:
            self.discharge_acbs(abs(shortage) * 1.1)

        print("Заряд аккумов:", self.get_full_acb_charge())

        # адрес линии в объекты
        endpoint2obj = dict()
        for obj in self.psm.objects:
            endpoint = obj.path[-1]
            if not (endpoint in endpoint2obj.keys()):
                endpoint2obj[endpoint] = list()
            endpoint2obj[endpoint].append(obj)

        # Если слишком высокий износ, то отключаем(если объекта нет в игнроре)
        for i, net in self.psm.networks.items():
            if net.location:
                if net.wear > CRITICAL_WEAR:
                    location = net.location
                    CAN_OFF = True
                    for obj in endpoint2obj[location]:
                        if obj.address[0] in IGNORE_GLOBAL_LINE_OFF:
                            # print(obj, "NOT OFF FOREVER")
                            CAN_OFF = False
                            break
                    if CAN_OFF:
                        line_obj = location[-1]
                        st_addr = self.id2obj[line_obj.id].address[0]
                        self.psm.orders.line_off(st_addr, line_obj.line)

        # Отключаем объекты, которые ОБЯЗАТЕЛЬНО выключить
        for obj in self.psm.objects:
            if obj.type == "main":
                continue

            if obj.address[0] in MUST_GLOBAL_LINE_OFF:
                obj_st, line_num = self.get_obj_st(obj)
                self.psm.orders.line_off(obj_st, line_num)

        # Ручная работа с АКБ
        if EMERGENCE_charge_acbs:
            self.charge_acbs(EMERGENCE_charge_acbs)
        if EMERGENCE_DIScharge_acbs:
            self.discharge_acbs(EMERGENCE_DIScharge_acbs)

        # if self.psm.tick < 10:
        #    if shortage < 0:
        #        self.psm.orders.buy(abs(shortage), 1)

        if self.psm.tick >= TICK_ENERGY_OUT:
            self.discharge_acbs(DISCHARGE_END_ENERGY)

        # self.charge_acbs(15) # зарядка акб
        # self.discharge_acbs(15) # разрядка акб
        # P.S. все линии каждый вход по умолчанию включаются, здесь указывайте их конечное состояние
        # self.psm.orders.line_on("e5", 1) # подключение линии (1-3)
        # self.psm.orders.line_off("e5", 1) # отключение линии (1-3)
        # self.psm.orders.sell(abs(shortage)*0.8, 10) # Заявка на продажу 10,2 МВт за 2,5 руб./МВт
        # self.psm.orders.buy(abs(shortage)*0.8, 1)# Заявка на покупку 5,5 МВт за 5,1 руб./МВт
        self.print_public_info()
        print(self.psm.orders.humanize())


psm = ips.init()
controller = MyController(psm)
controller.run()
controller.close()
