import requests


def do_something():
    requests.get("something")


def tps(tps_name, fuel):
    data = {"tps": tps_name, "fuel": fuel}
    requests.post("server/orders", json=data)
# psm.orders.tps("t1", 5)
