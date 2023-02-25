class Stand:
    def __init__(self):
        self.load_topol()

    def tps(self, name_tps, fuel):
        power = fuel * 2
        self.stations[name_tps].power = power

    def run_sim(self, script_func):
        for i in range(ticks):
            script_func(self)
