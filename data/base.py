from data.line import Line


class Base:
    def __init__(self, name, connections):
        self.name = name
        self.connections = connections
        type_name = name[0]
        if type_name == "M":
            self.type = "main"
        elif type_name == "e":
            self.type = "miniA"
        elif type_name == "f":
            self.type = "factory"
        elif type_name == "c":
            self.type = "storage"
        elif type_name == "h":
            self.type = "houseA"
        elif type_name == "d":
            self.type = "houseB"
        elif type_name == "s":
            self.type = "solar"
        elif type_name == "b":
            self.type = "hospital"
        elif type_name == "s":
            self.type = "hospital"
        else:
            raise ValueError(f"Нет такого типа объектов {name}")

    def append_connection(self, line: Line):
        self.connections.append(line)
