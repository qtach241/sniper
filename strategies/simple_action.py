from enum import Enum
from abc import ABC, abstractmethod

class ActionSpace(Enum):
    HOLD = 1
    MARKET_ORDER_BUY_ALL = 2
    MARKET_ORDER_SELL_ALL = 3
    MARKET_ORDER_BUY_TENTH = 4
    MARKET_ORDER_SELL_TENTH = 5

class Action(ABC):
    def __init__(self, agent, id) -> None:
        self._agent = agent
        self._id = id

    @property
    def action_id(self) -> ActionSpace:
        return id

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def simulate(self):
        pass

class Action_Hold(Action):
    def __init__(self, agent) -> None:
        super().__init__(agent, id=ActionSpace.HOLD)
    
    def execute(self):
        print("Executing HOLD action")
        print(self._agent._df)

    def simulate(self):
        print("Simulating HOLD action")
        print(self._agent._df)

class Action_BuyAll(Action):
    def __init__(self, agent) -> None:
        super().__init__(agent, id=ActionSpace.MARKET_ORDER_BUY_ALL)

    def execute(self):
        pass

    def simulate(self):
        # Check the current state, if QTY of USD is greater than 0, transfer
        # all USD to the crypto asset at the current bid.
        pass
