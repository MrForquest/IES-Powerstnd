import ips
import numpy as np

for I in range(2, 100):
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
    psm = ips.from_log("logs/game.json", step=I)

    station_names = {"main", "miniA", "miniB"}
    past_tick = max(psm.tick - 1, 0)
    next_tick = min(psm.tick + 1, len(psm.forecasts.houseA) - 1)

    accums = ["c5"]
    prices = {"d3": 7.2, "h6": 5}
    table = "S1c16"
    # tables ['S1c16', 'S1c15', 'S1a3', 'S1c17', 'S1c14', 'S1c13', 'S1c11']
    now_wind = max(psm.forecasts.wind[table][psm.tick], 0)
    next_wind = max(psm.forecasts.wind[table][next_tick], 0)
    past_sun = max(psm.forecasts.sun[past_tick], 0)
    now_sun = max(psm.forecasts.sun[psm.tick], 0)
    next_sun = max(psm.forecasts.sun[next_tick], 0)

    consumption = 0  # прогноз суммарного потребления
    generation = 0  # прогноз суммарной генерации


    def sun_formule(x, y):
        # print(x, ",", y)
        f0 = np.array([1] * len(x))
        gen = np.array(x)
        sun = np.array(y)

        sun[sun < 0] = 0
        gen[sun < 0] = 0

        gen[gen < 0.1] = 0
        sun[gen < 0.1] = 0

        Y = sun.reshape(-1, 1)
        w = np.array([np.nan, np.nan])
        X = np.array([f0, gen]).T
        coef_matrix = np.dot(np.dot(np.linalg.inv(np.dot(X.T, X)), X.T), Y)

        b = coef_matrix.T[0][0]
        coef = coef_matrix.T[0][1]

        # рассчитаем коэффициенты используя формулу
        return coef, b


    def print_object(obj):
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
        print("Потребление за первый ход:",
              obj.power.then[0].consumed)
        print("Заряд (актуально для накопителя):",
              obj.charge.now)  # float


    print("Тик", psm.tick)
    for obj in psm.objects:
        # print_object(obj)

        if obj.type == "solar":
            # вычисляем прогноз солнца
            # print("Реальность предыдущего:", obj.power.now.generated)
            corr_next_sun = max(0, next_sun - 0.5)

            if psm.tick >= 50:
                obj_gens = [line.generated for line in obj.power.then]
                coef_, b_ = sun_formule(psm.sun.then, obj_gens)
                energy = next_sun * coef_ + b_
                # print("Параметры панели", coef_, b_)
                energy = max(min(15, energy), 0)
                # print("Предсказание", energy)
                generation += energy
            else:
                if now_sun == 0:
                    # print("Предсказание", 0)
                    generation += 0
                else:
                    # print("Предсказание", obj.power.now.generated * (corr_next_sun / now_sun), now_sun, corr_next_sun,
                    #      corr_next_sun / now_sun)
                    generation += obj.power.now.generated * (corr_next_sun / now_sun)

            continue

            # вычисляем прогноз потребления
        if obj.type == "housea":
            additional = 0.82 * (5 - prices[addr]) ** 2.6 if prices[addr] < 5 else 0
            consumption += psm.forecasts.houseA[next_tick] + additional + 0.5
        if obj.type == "houseb":
            additional = 0.24 * (9 - prices[addr]) ** 2.2 if prices[addr] < 8 else 0
            consumption += psm.forecasts.houseB[next_tick] + additional + 0.5
        if obj.type == "factory":
            consumption += psm.forecasts.factory[next_tick] + 0.5
        if obj.type == "hospital":
            consumption += psm.forecasts.hospital[next_tick] + 0.5

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


    def print_net(index, net):
        print("== Энергорайон", index, "==")
        print("Адрес:", net.location)
        # (ID подстанции, № линии)]
        print("Включен:", net.online)  # bool
        print("Генерация:", net.upflow)  # float
        print("Потребление:", net.downflow)  # float
        print("Потери:", net.losses)  # float
        print("Износ ветки:", net.wear)  # float


    for index, net in psm.networks.items():
        # if net.wear >= 0.85:
        #    psm.orders.line_off(*net.location)
        break
        print(print_net(index, net))

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
    print("конец")
    psm.orders.humanize()
