import ips
import numpy as np

obj_types = [
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
psm = ips.init()

station_names = {"main", "miniA", "miniB"}
past_tick = max(psm.tick - 1, 0)
next_tick = min(psm.tick + 1, len(psm.forecasts.houseA) - 1)

accums = ["c5"]
prices = {"d3": 7.2, "h6": 5}
table = "1"

now_wind = psm.forecasts.wind[table][psm.tick]
next_wind = psm.forecasts.wind[table][next_tick]
past_sun = psm.forecasts.sun[past_tick]
now_sun = psm.forecasts.sun[psm.tick]
next_sun = psm.forecasts.sun[next_tick]

consumption = 0  # прогноз суммарного потребления
generation = 0  # прогноз суммарной генерации


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

    addr = obj.address[0]
    if obj.type in station_names:
        # включаем линии
        for i in range(2 if obj.type == "miniB" else 3):
            psm.orders.line_on(addr, i + 1)
        continue
    if obj.type == "wind":
        # вычисляем прогноз ветра
        if now_wind <= next_wind:
            generation += obj.power.now.generated * 1.10
        else:  # now_wind > next_wind
            generation += obj.power.now.generated * 0.85
        continue
    if obj.type == "solar":
        # вычисляем прогноз солнца
        if psm.tick >= 2:
            coef_, b_ = sun_formule(psm.sun.then, obj.score.then)
            energy = next_sun * coef_ + b_
            energy = max(min(15, energy), 0)
            generation += energy
        else:
            if now_sun <= next_sun:
                generation += obj.power.now.generated * 1.05
            else:  # now_sun > next_sun
                generation += obj.power.now.generated * 0.85
        continue

    # вычисляем прогноз потребления
    if obj.type == "housea":
        additional = 0.82 * (5 - prices[addr]) ** 2.6 if prices[addr] < 5 else 0
        consumption += psm.forecasts.houseA[next_tick] + additional
    if obj.type == "houseb":
        additional = 0.24 * (9 - prices[addr]) ** 2.2 if prices[addr] < 8 else 0
        consumption += psm.forecasts.houseB[next_tick] + additional
    if obj.type == "factory":
        consumption += psm.forecasts.factory[next_tick]
    if obj.type == "hospital":
        consumption += psm.forecasts.hospital[next_tick]

shortage = abs(generation) - abs(consumption) - (consumption / psm.total_power.consumed) * psm.total_power.losses
print("SHORT", shortage)


def charge_acbs(energy):
    d_eng = max(min((energy / len(accums)), 15), 0)
    for acb in accums:
        psm.orders.charge(acb, d_eng)


def discharge_acbs(energy):
    d_eng = max(min((energy / len(accums)), 15), 0)
    for acb in accums:
        psm.orders.discharge(acb, d_eng)


if shortage > 0:
    # psm.orders.charge("c3", abs(shortage))
    charge_acbs(abs(shortage))
if shortage < 0:
    # psm.orders.discharge("c3", abs(shortage))
    discharge_acbs(abs(shortage))

for index, net in psm.networks.items():
    print("== Энергорайон", index, "==")
    print("Адрес:", net.location)
    # (ID подстанции, № линии)]
    print("Включен:", net.online)  # bool
    print("Генерация:", net.upflow)  # float
    print("Потребление:", net.downflow)  # float
    print("Потери:", net.losses)  # float
    print("Износ ветки:", net.wear)  # float

    # if net.wear >= 0.85:
    #    psm.orders.line_off(*net.location)

print("Ход:", psm.tick)  # int
print("Всего ходов:", psm.gameLength)  # int
print("Изменение счёта:", psm.scoreDelta)  # float
print("Всего сгенерировано:",
      psm.total_power.generated)  # float
print("Всего потреблено:",
      psm.total_power.consumed)  # float
print("Получено с биржи (минус = отправлено):",
      psm.total_power.external)  # float
print("Всего потерь:",
      psm.total_power.losses)  # float
print("-" * 20)
psm.save_and_exit()
