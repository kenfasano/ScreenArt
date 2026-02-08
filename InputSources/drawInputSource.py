from abc import abstractmethod
from . import inputSource

class DrawInputSource(inputSource.InputSource):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def draw(self, filename: str, *args, **kwargs):
        ...
