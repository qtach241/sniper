from enum import Enum
from abc import ABC, abstractmethod

class ActionSpace(Enum):
    HOLD = 1
    MARKET_ORDER_BUY_ALL = 2
    MARKET_ORDER_SELL_ALL = 3
    MARKET_ORDER_BUY_TENTH = 4
    MARKET_ORDER_SELL_TENTH = 5

class Action(ABC):
    def __init__(self, agent, id, cd) -> None:
        self._agent = agent
        self._id = id
        self._cd = cd

        self._start_time = 0

    @property
    def action_id(self) -> ActionSpace:
        return self._id

    def time_til(self):
        return self._start_time + self._cd - self._agent._clock.get_time()

    def execute(self):
        if self.time_til() <= 0:
            self._start_time = self._agent._clock.get_time()
            self.on_execute()
        else:
            print(f"Action {self.action_id} on CD for {self.time_til()} seconds!")
            pass

    def simulate(self):
        if self.time_til() <= 0:
            self._start_time = self._agent._clock.get_time()
            self.on_simulate()
        else:
            print(f"Action {self.action_id} on CD for {self.time_til()} seconds!")
            pass

    @abstractmethod
    def on_execute(self):
        pass

    @abstractmethod
    def on_simulate(self):
        pass

class Action_Hold(Action):
    def __init__(self, agent, cd) -> None:
        super().__init__(agent, id=ActionSpace.HOLD, cd=cd)
    
    def on_execute(self):
        print("Executing HOLD action")
        print(self._agent._df)

    def on_simulate(self):
        print("Simulating HOLD action")
        print(self._agent._df)

class Action_BuyAll(Action):
    def __init__(self, agent, cd) -> None:
        super().__init__(agent, id=ActionSpace.MARKET_ORDER_BUY_ALL, cd=cd)

    def on_execute(self):
        print("Executing BUY ALL action")
        print(self._agent._df)

    def on_simulate(self):
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
    def __init__(self, agent, cd) -> None:
        super().__init__(agent, id=ActionSpace.MARKET_ORDER_SELL_ALL, cd=cd)

    def on_execute(self):
        print("Executing SELL ALL action")
        print(self._agent._df)

    def on_simulate(self):
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
