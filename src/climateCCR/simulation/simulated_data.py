from abc import abstractmethod


class SimulatedData:
    def __init__(self) -> None:
        pass

    @abstractmethod
    def get_value(self, **kwargs):
        pass
