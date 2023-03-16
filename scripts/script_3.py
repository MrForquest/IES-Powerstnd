import ips_past
import math
import numpy as np

psm = ips_past.init()

""" 
Очень базовый скрипт для стенда ИЭС.
1. Включает все линии
2. Наивно предсказывает генерацию по СЭC/ВЭС (по медиане)
3. И ничего больше не делает.
"""


def sun_formule(x, y):
    f0 = np.array([1] * len(x))
    f1 = np.array(x)
    Y = np.array([[dy] for dy in y])
    w = np.array([np.nan, np.nan])
    X = np.array([f0, f1]).T
    coef_matrix = np.dot(np.dot(np.linalg.inv(np.dot(X.T, X)), X.T), Y)

    b = coef_matrix.T[0][0]
    coef = coef_matrix.T[0][1]

    # рассчитаем коэффициенты используя формулу
    return coef, b


station_names = {"main", "miniA", "miniB"}

past_tick = max(psm.tick - 1, 0)
next_tick = min(psm.tick + 1, len(psm.forecasts.houseA[0]) - 1)

now_wind = psm.forecasts.wind[0][psm.tick]
next_wind = psm.forecasts.wind[0][next_tick]

past_sun = psm.forecasts.sun[0][past_tick]
now_sun = psm.forecasts.sun[0][psm.tick]
next_sun = psm.forecasts.sun[0][next_tick]

consumption = 0  # прогноз суммарного потребления
generation = 0  # прогноз суммарной генерации

for obj in psm.objects:
    addr = obj.address[0]
    if obj.type in station_names:
        # включаем линии
        for i in range(2 if obj.type == "miniB" else 3):
            psm.orders.line_on(addr, i + 1)
        continue
    if obj.type == "wind":
        # вычисляем прогноз ветра по медиане
        if now_wind <= next_wind:
            generation += obj.power.now.generated * 1.10
        else:  # now_wind > next_wind
            generation += obj.power.now.generated * 0.85
        continue
    if obj.type == "solar":
        # вычисляем прогноз солнца по медиане
        if psm.tick >= 2:
            coef_, b_ = sun_formule(psm.sun.then, obj.score.then)
            energy = next_sun * coef_ + b_
            energy = max(min(15, energy), 0)
            generation += energy

        if now_sun <= next_sun:
            generation += obj.power.now.generated * 1.05
        else:  # now_sun > next_sun
            generation += obj.power.now.generated * 0.85
        continue
    # вычисляем прогноз потребления по медиане
    if obj.type == "housea":
        consumption += psm.forecasts.houseA[0][next_tick]
    if obj.type == "houseb":
        consumption += psm.forecasts.houseB[0][next_tick]
    if obj.type == "factory":
        consumption += psm.forecasts.factory[0][next_tick]
    if obj.type == "hospital":
        consumption += psm.forecasts.hospital[0][next_tick]

# generation, consumption = psm.total_power.generated, psm.total_power.consumed

shortage = abs(generation) - abs(consumption)

for obj in psm.objects:
    addr = obj.address[0]

    # last_energy += obj.power.now.generated

for index, net in psm.networks.items():
    # print("== Энергорайон", index, "==")
    print(net.location)

# shortage = (max(shortage, 0) + 20) / 2
# last_energy = last_energy / 2
print("SHORT", shortage)

acbs = ["cB", "cA"]


def charge_acb(energy):
    psm.orders.charge(acbs[0], energy / 2)
    psm.orders.charge(acbs[1], energy / 2)


def discharge_acb(energy):
    # obj.charge.now
    psm.orders.discharge(acbs[0], energy / 2)
    psm.orders.discharge(acbs[1], energy / 2)


if shortage > 0:
    # psm.orders.charge("c3", abs(shortage))
    charge_acb(abs(shortage))
if shortage < 0:
    # psm.orders.discharge("c3", abs(shortage))
    discharge_acb(abs(shortage))

for index, net in psm.networks.items():
    print("== Энергорайон", index, "==")
    print("Адрес:", net.location)
    # (ID подстанции, № линии)]
    print("Включен:", net.online)  # bool
    print("Генерация:", net.upflow)  # float
    print("Потребление:", net.downflow)  # float
    print("Потери:", net.losses)  # float
    print("Усталость ветки:", net.wear)  # float
    print("Оставшееся время восстановления",
          "после аварии:", net.broken)  # int

psm.orders.add_graph(0, psm.forecasts.houseA[0])
psm.orders.add_graph(0, psm.forecasts.houseB[0])
psm.orders.add_graph(0, psm.forecasts.factory[0])
psm.orders.add_graph(0, psm.forecasts.hospital[0])
psm.orders.add_graph(0, psm.forecasts.sun[0])
psm.orders.add_graph(0, psm.forecasts.wind[0])
psm.orders.add_graph(1, [i for i in range(psm.tick)])
psm.orders.add_graph(2, [math.inf, math.nan])
psm.orders.add_graph(10, [math.inf, math.nan])

print(psm.orders.humanize())

print("Data:")
print("Тик", psm.tick)
for obj in psm.objects:
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
    print("Доход за первый ход:",
          obj.score.then[0].income)
    print("Расход за 5ый ход:",
          obj.score.then[4].loss)  # float
    print("Генерация:",
          obj.power.now.generated)  # float
    print("Потребление:",
          obj.power.now.consumed)  # float
    print("Потребление за первый ход:",
          obj.power.then[0].consumed)
    print("Заряд (актуально для накопителя):",
          obj.charge.now)  # float
    print("Модули подстанции:",
          obj.modules)  # [Cell или Diesel]
    print("Полный power.then",
          obj.power.then)
    print("Полный power.now",
          obj.power.now)

print("END DATA")
psm.save_and_exit()
