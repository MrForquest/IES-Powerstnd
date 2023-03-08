from data.factory import FactoryOutput, Factory


class Hospital(Factory):
    def __init__(self, output_obj1, output_obj2=None):
        self.output_obj1 = output_obj1
        self.output_obj2 = output_obj2
        self.output_obj1.set_factory(self)
        if not (output_obj2 is None):
            self.output_obj2.set_hospital(self)
        super().__init__("f-AbstractHospital")

    def __repr__(self):
        return f'Hospital("{self.output_obj1},{self.output_obj2})")'


class HospitalOutput(FactoryOutput):
    def __init__(self, name, hospital=None, connections=None):
        if connections is None:
            connections = list()
        super().__init__(name, connections)
        self.connections = connections
        self.hospital = hospital

    def get_energy(self, tick):
        return self.hospital.get_energy(tick)

    def get_penalty(self, tick):
        return self.hospital.get_penalty(tick)

    def set_hospital(self, hospital):
        self.hospital = hospital

    def __repr__(self):
        return f'HospitalOutput("{self.name}")'
