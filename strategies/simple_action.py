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
        print("Executing BUY ALL action")
        print(self._agent._df)

    def simulate(self):
        # Transfer all USD to the crypto asset (ie. BUY) at the current ask price.
        print("Simulating BUY ALL action")
        c_qty_usd = self._agent._df.at[self._agent._df.index[-1], 'qty_usd']
        c_qty_ass = self._agent._df.at[self._agent._df.index[-1], 'qty_crypto']
        c_bid = self._agent._df.at[self._agent._df.index[-1], 'bid']
        c_ask = self._agent._df.at[self._agent._df.index[-1], 'ask']
        
        n_qty_usd = 0
        n_qty_ass = c_qty_ass + (c_qty_usd/c_ask)

        # Modify the last row in place with the new qty values
        self._agent._df.at[self._agent._df.index[-1], 'qty_usd'] = n_qty_usd
        self._agent._df.at[self._agent._df.index[-1], 'qty_crypto'] = n_qty_ass
        self._agent._df.at[self._agent._df.index[-1], 'networth'] = n_qty_ass*c_bid
        print(self._agent._df)

class Action_SellAll(Action):
    def __init__(self, agent) -> None:
        super().__init__(agent, id=ActionSpace.MARKET_ORDER_SELL_ALL)

    def execute(self):
        print("Executing SELL ALL action")
        print(self._agent._df)

    def simulate(self):
        # Transfer all crypto assets to USD (ie. SELL) at the current bid price.
        print("Simulating SELL ALL action")
        c_qty_usd = self._agent._df.at[self._agent._df.index[-1], 'qty_usd']
        c_qty_ass = self._agent._df.at[self._agent._df.index[-1], 'qty_crypto']
        c_bid = self._agent._df.at[self._agent._df.index[-1], 'bid']
        
        n_qty_usd = c_qty_usd + (c_qty_ass*c_bid)
        n_qty_ass = 0

        # Modify the last row in place with the new qty values
        self._agent._df.at[self._agent._df.index[-1], 'qty_usd'] = n_qty_usd
        self._agent._df.at[self._agent._df.index[-1], 'qty_crypto'] = n_qty_ass
        self._agent._df.at[self._agent._df.index[-1], 'networth'] = n_qty_usd
        print(self._agent._df)
