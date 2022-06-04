class Station(Base):
    def __init__(self, name, connections=None, lines_=None):
        if connections is None:
            connections = list()
        if lines_ is None:
            lines_ = list()
        super().__init__(name, connections)
        self.lines = lines_

    def set_lines(self, lines: List[Line]):
        self.lines = lines

    def get_lines(self):
        return self.lines

    def append_line(self, line: Line):
        self.lines.append(line)

    def __repr__(self):
        return f"Station(\"{self.name}\")"
