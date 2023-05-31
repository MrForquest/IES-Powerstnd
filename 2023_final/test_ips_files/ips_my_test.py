import ips_past
import math

psm = ips_past.init()

""" 
Очень базовый скрипт для стенда ИЭС.
1. Включает все линии
2. Наивно предсказывает генерацию по СЭC/ВЭС (по медиане)
3. И ничего больше не делает.
"""

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

sell_price = 5
buy_price = 2
lishn = psm.total_power.generated - psm.total_power.consumed
if lishn > 0:
    psm.orders.sell(lishn, sell_price)
elif lishn < 0:
    psm.orders.buy(lishn, buy_price)
shortage = consumption - generation

last_energy_9 = 0
last_energy_A = 0
last_energy = 0
for obj in psm.objects:
    addr = obj.address[0]
    if obj.type == "TPS":
        last_energy += obj.power.now.generated


def get_tes_power(fumes, last_energy_):
    kpd = (-0.78125 * (fumes**2) + 12.5 * fumes + 40) / 100
    if last_energy_ > 0.5:
        energy = fumes * kpd + 0.6 * (last_energy_ - 0.5)
    else:
        energy = fumes * kpd
    return energy


def solve_equation_tes(a_, b_, c_, d_):
    a = b_ / a_
    b = c_ / a_
    c = d_ / a_
    q = (a**2 - 3 * b) / 9
    r = (2 * (a**3) - 9 * a * b + 27 * c) / 54
    s = (q**3) - (r**2)
    # q>0 всегда, про s не уверен
    if s > 0:
        if q > 0:
            f = math.acos(r / math.sqrt(q**3)) / 3
            x1 = -2 * math.sqrt(q) * math.cos(f) - a / 3
            x2 = -2 * math.sqrt(q) * math.cos(f + ((2 * math.pi) / 3)) - a / 3
            x3 = -2 * math.sqrt(q) * math.cos(f - ((2 * math.pi) / 3)) - a / 3
            return x1, x2, x3
    else:
        if q > 0:
            # print(abs(r) / (abs(q) ** 3))
            f = math.acosh(abs(r) / math.sqrt(q**3)) / 3
            k = 0 if r == 0 else (1 if r > 0 else -1)
            x1 = -2 * k * math.sqrt(abs(q)) * math.cosh(f) - a / 3
            return (x1,)
    return (0,)


def get_num_fumes(p):
    last = last_energy
    if last > 0.5:
        d = 60 * (last - 0.5) - 100 * p
    else:
        d = -100 * p
    x = solve_equation_tes(-0.78125, 12.5, 40, d)
    x = list(filter(lambda s: s > 0, x))
    if len(x) > 0:
        x = min(min(x), 10)
        fum = x
        if fum == 10:
            if abs(p - get_tes_power(10, last)) < abs(p - get_tes_power(0, last)):
                fum = 10
            else:
                fum = 0
    else:
        if get_tes_power(10, last) < p:
            fum = 10
        else:
            fum = 0
    return fum


line_11_wear = 0
line_12_wear = 0
line_21_wear = 0
line_22_wear = 0

for index, net in psm.networks.items():
    # print("== Энергорайон", index, "==")
    print(net.location)
    if ips_past.Line(("miniB", 1), 1) in net.location:
        line_11_wear = net.wear
    if ips_past.Line(("miniA", 1), 1) in net.location:
        line_12_wear = net.wear

if psm.tick < 5:
    psm.orders.line_off("m1", 1)
else:
    wall = 0.4
    if line_11_wear < wall and line_12_wear < wall:
        pass
    elif line_11_wear > wall:
        psm.orders.line_off("m1", 1)
    elif line_12_wear > wall:
        psm.orders.line_off("e1", 1)

shortage = max(shortage, 0) + 3

print("SHORT", shortage)

if shortage > 0:
    fu = get_num_fumes(shortage)
    print(
        f"В ТЭС tF загружено {fu} и получено {get_tes_power(fu, last_energy)} МВт и цена за это {fu * 3.5} руб",
        f"На прошлом ходу было произведено {last_energy}МВт",
    )
    psm.orders.tps("tF", fu)

for index, net in psm.networks.items():
    print("== Энергорайон", index, "==")
    print("Адрес:", net.location)
    # (ID подстанции, № линии)]
    print("Включен:", net.online)  # bool
    print("Генерация:", net.upflow)  # float
    print("Потребление:", net.downflow)  # float
    print("Потери:", net.losses)  # float
    print("Усталость ветки:", net.wear)  # float
    print("Оставшееся время восстановления", "после аварии:", net.broken)  # int

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
psm.save_and_exit()
