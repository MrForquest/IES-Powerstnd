class EnergyRegion:
    def __init__(self, line):
        self.wear = 0
        self.online = False
        self.upflow = 0
        self.downflow = 0
        self.losses = 0
        self.broken = False
        self.line = line

    def location(self):
        return self.line.station.id, self.line.line_id

    def __repr__(self):
        return f"Net: {self.location()}"
