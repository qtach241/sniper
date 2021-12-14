from abc import ABC, abstractmethod

class L2OrderBook(ABC):

    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def destroy(self):
        pass

    @abstractmethod
    def export(self):
        pass