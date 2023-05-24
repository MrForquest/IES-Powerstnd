import matplotlib.pyplot as plt
import numpy as np


def get_energy_loss(energy):
    energy = abs(energy)
    coef_loss = ((energy / 50) ** 2.4) * 0.6

    return coef_loss


def homeA_cons(price):
    return (0.82 * (5 - price) ** 2.6 if price < 5 else 0)


def homeB_cons(price):
    return (0.24 * (9 - price) ** 2.2 if price < 8 else 0)


def get_wear_loss(wear):
    return (wear ** 2) * 0.5


def get_wear(energy):
    w = ((abs(energy) / 50) ** 1.9) / 2
    return w


def full_loss(wear, energy):
    energy = abs(energy)
    return (1 - (1 - get_wear_loss(wear)) * (1 - get_energy_loss(energy))) * energy


def run(price, forecast, wear_bold=1):
    wear = 0
    money = 0
    total_cons = 0
    turn_on = True
    total_energy_cons = list()
    for val in forecast:
        if wear > wear_bold:
            turn_on = False
        else:
            turn_on = True
        if not turn_on:
            wear = max(0, wear - 1)
            energy = val + homeB_cons(price)
            money -= energy * price * 2
        energy = val + homeB_cons(price)
        energy_loss = full_loss(wear, energy)
        all_energy = energy + energy_loss
        total_cons += all_energy
        wear += get_wear(all_energy)
        wear = min(1, wear)
        money += energy * price
        # print("Потребление только дома", val, "Потребление майнера:", homeA_cons(price), "Потери", energy_loss,
        #      "Суммарное потребление", all_energy, "Износ", wear)
        total_energy_cons.append(all_energy)
    return money, total_cons, wear, price, total_energy_cons


forecast = [1.72733370974882, 1.1023404933645313, 0.8257151476481921, 0.8506824314402289, 0.8633077968682212,
            0.9100066274402081, 0.7964874389026317, 0.669095855915502, 1.0731976099090574, 0.692778142551282,
            1.0744217533702427, 0.9427466489739071, 1.2957407139258803, 1.0579419234259129, 1.2154168210283938,
            1.2218353157003787, 1.5890098087851223, 1.845683118586905, 1.9665946038627116, 2.0502890163913654,
            1.9124682314899468, 1.8876568273427414, 2.0336060239239817, 1.8862813099304168, 1.5649508729596042,
            1.275547996953325, 1.110438904143322, 1.2740592377486872, 0.9885653031806207, 1.3114334091145388,
            1.277887510809852, 1.6016000962407615, 1.8204765785349972, 2.188731712079769, 2.0795224925362277,
            2.1323447303776346, 2.568913555087682, 3.148083675704668, 3.169519704979591, 3.7035846974282394,
            4.1413765608333035, 4.440666249213219, 4.515027344952685, 4.181833003177746, 3.2658099357683263,
            2.553150108803367, 2.4928306386919226, 2.15875476958349, 1.2575594641297552, 1.0130835178716562,
            0.5974024900422192, 1.002087368283458, 0.4961819088005325, 0.6948497601548932, 0.7754059759107612,
            0.7473955495910555, 0.7856424334300118, 0.707836437189997, 0.9245448534581786, 1.327700838706747,
            0.9048113672590519, 1.2924917816306334, 1.485982908424574, 1.407547495504878, 1.5194564243417767,
            1.4386388467271578, 1.4700323810043097, 1.98042009354626, 1.7472889140831145, 1.8689969040728072,
            1.7389453891805857, 1.552537920267184, 1.4246011340017701, 1.0420483458519185, 1.4570568881578976,
            0.9472116990216994, 0.8222737299726064, 1.0540438914197574, 1.1628915182056012, 1.3666730105637719,
            1.6707334628291857, 1.8415481889684195, 2.074645952031451, 2.3278410427783425, 3.001263973472515,
            3.196685334864472, 3.4007601771197034, 3.791334999910317, 4.3623572807304125, 4.6237820782637975,
            4.578211075088921, 4.090472301712667, 3.399783848241042, 2.8746592867518377, 2.6481402385548822,
            2.262063853093361, 1.7079916374985125, 1.017279417978716, 0.9199757066987317, 0.7502175805999975
            ]
money, total_cons, wear, price, total_energy_cons = run(6.8, forecast, wear_bold=1)
total_energy_cons = np.array(total_energy_cons)

# print(money, total_cons, total_energy_cons.max())
print(sum(forecast) * 6.8)
# exit()
moneys = list()
prices = list()
all_data = list()
rac = list()
for price in range(100, 1000):
    p = price / 100
    m = run(p, forecast, wear_bold=1)
    all_data.append(m)
    moneys.append(m[0])
    rac.append(m[0] / m[1])
    prices.append(p)
print(all_data)
print(max(all_data, key=lambda s: s[0]))
x_lim = np.linspace(0, 10, num=21)
fig, ax = plt.subplots(2, figsize=(12, 6))
ax[0].plot(prices, moneys)
ax[1].plot(prices, rac)

ax[0].grid(visible=True)
ax[1].grid(visible=True)

plt.xticks(x_lim)
plt.show()
print(sum(forecast) * 9.99)
