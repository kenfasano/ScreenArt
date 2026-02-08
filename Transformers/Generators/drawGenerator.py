from abc import ABC, abstractmethod

# REF_CHANGE: Renamed Class
class DrawGenerator(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def draw(self, *args, **kwargs):
        pass
