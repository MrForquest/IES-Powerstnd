from data.line import Line


class Base:
    def __init__(self, name, connections):
        self.name = name
        self.connections = connections

    def append_connection(self, line: Line):
        self.connections.append(line)
