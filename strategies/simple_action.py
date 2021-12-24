from enum import Enum
from abc import ABC, abstractmethod

class ActionSpace(Enum):
    HOLD = 1
    BUY_ALL = 2
    SELL_ALL = 3

class Action(ABC):

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def simulate(self):
        pass

class Action_BuyAll(Action):

    id = ActionSpace.BUY_ALL

    def execute(self):
        pass

    def simulate(self):
        pass
