class Line:
    def __init__(self, station, line_id, address=None):
        if address is None:
            address = list()
        self.station = station
        self.address = address
        self.line_id = line_id

    def append_address(self, address):
        self.address.append(address)

    def get_station(self):
        return self.station

    def get_address(self):
        return self.address

    def get_line_id(self):
        return self.line_id

    def __repr__(self):
        return f"Line{self.line_id} {self.station} to {self.address}"
