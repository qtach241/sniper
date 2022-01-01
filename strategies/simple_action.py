from enum import Enum
from abc import ABC, abstractmethod

class ActionSpace(Enum):
    HOLD = 1
    MARKET_ORDER_BUY_ALL = 2
    MARKET_ORDER_SELL_ALL = 3
    MARKET_ORDER_BUY_100 = 4
    MARKET_ORDER_SELL_100 = 5

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
            #print(f"Action {self.action_id} on CD for {self.time_til()} seconds!")
            pass

    def simulate(self):
        if self.time_til() <= 0:
            self._start_time = self._agent._clock.get_time()
            self.on_simulate()
        else:
            #print(f"Action {self.action_id} on CD for {self.time_til()} seconds!")
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
        # Do nothing
        pass

    def on_simulate(self):
        # Do nothing
        pass

class Action_BuyAll(Action):
    def __init__(self, agent, cd) -> None:
        super().__init__(agent, id=ActionSpace.MARKET_ORDER_BUY_ALL, cd=cd)

    def on_execute(self):
        pass

    def on_simulate(self):
        # Transfer all USD to the crypto asset (ie. BUY) at the current ask price.
        c_qty_usd = self._agent._df.at[self._agent._df.index[-1], 'qty_usd']
        c_qty_ass = self._agent._df.at[self._agent._df.index[-1], 'qty_crypto']
        c_ask = self._agent._df.at[self._agent._df.index[-1], 'ask']

        usd_to_xfer = c_qty_usd
        fee_usd = usd_to_xfer * self._agent.fee_rate
        
        n_qty_usd = 0
        n_qty_ass = c_qty_ass + ((usd_to_xfer-fee_usd)/c_ask)

        # Modify the last row in place with the new qty values
        self._agent.update_tail(n_qty_usd, n_qty_ass)
        print(f"{self._agent._clock.get_time()}: ",
            f"{self._agent.__class__.__name__}-{self._agent.fee_rate} BOUGHT {(usd_to_xfer-fee_usd)/c_ask} crypto for {usd_to_xfer} USD ",
            f"(U: {n_qty_usd}, C: {n_qty_ass}, N: {self._agent._df.at[self._agent._df.index[-1], 'networth']})")

class Action_SellAll(Action):
    def __init__(self, agent, cd) -> None:
        super().__init__(agent, id=ActionSpace.MARKET_ORDER_SELL_ALL, cd=cd)

    def on_execute(self):
        pass

    def on_simulate(self):
        # Transfer all crypto assets to USD (ie. SELL) at the current bid price.
        c_qty_usd = self._agent._df.at[self._agent._df.index[-1], 'qty_usd']
        c_qty_ass = self._agent._df.at[self._agent._df.index[-1], 'qty_crypto']
        c_bid = self._agent._df.at[self._agent._df.index[-1], 'bid']
        
        ass_to_xfer = c_qty_ass
        fee_usd = (ass_to_xfer*c_bid) * self._agent.fee_rate

        n_qty_usd = c_qty_usd + (ass_to_xfer*c_bid) - fee_usd
        n_qty_ass = 0

        # Modify the last row in place with the new qty values
        self._agent.update_tail(n_qty_usd, n_qty_ass)
        print(f"{self._agent._clock.get_time()}: ",
            f"{self._agent.__class__.__name__}-{self._agent.fee_rate} SOLD {ass_to_xfer} crypto for {(ass_to_xfer*c_bid) - fee_usd} USD ",
            f"(U: {n_qty_usd}, C: {n_qty_ass}, N: {self._agent._df.at[self._agent._df.index[-1], 'networth']})")

class Action_Buy100(Action):
    def __init__(self, agent, cd) -> None:
        super().__init__(agent, id=ActionSpace.MARKET_ORDER_BUY_100, cd=cd)

    def on_execute(self):
        pass

    def on_simulate(self):
        # Transfer 100 USD to the crypto asset (ie. BUY) at the current ask price.
        c_qty_usd = self._agent._df.at[self._agent._df.index[-1], 'qty_usd']
        c_qty_ass = self._agent._df.at[self._agent._df.index[-1], 'qty_crypto']
        c_ask = self._agent._df.at[self._agent._df.index[-1], 'ask']
        
        usd_to_xfer = 100 if c_qty_usd >= 100 else c_qty_usd
        fee_usd = usd_to_xfer * self._agent.fee_rate

        n_qty_usd = c_qty_usd - usd_to_xfer
        n_qty_ass = c_qty_ass + ((usd_to_xfer-fee_usd)/c_ask)

        # Modify the last row in place with the new qty values
        self._agent.update_tail(n_qty_usd, n_qty_ass)
        print(f"{self._agent._clock.get_time()}: ",
            f"{self._agent.__class__.__name__}-{self._agent.fee_rate} BOUGHT {(usd_to_xfer-fee_usd)/c_ask} crypto for {usd_to_xfer} USD ",
            f"(U: {n_qty_usd}, C: {n_qty_ass}, N: {self._agent._df.at[self._agent._df.index[-1], 'networth']})")

class Action_Sell100(Action):
    def __init__(self, agent, cd) -> None:
        super().__init__(agent, id=ActionSpace.MARKET_ORDER_SELL_100, cd=cd)

    def on_execute(self):
        pass

    def on_simulate(self):
        # Transfer 100 USD worth of crypto asset to USD (ie. SELL) at the current bid price.
        c_qty_usd = self._agent._df.at[self._agent._df.index[-1], 'qty_usd']
        c_qty_ass = self._agent._df.at[self._agent._df.index[-1], 'qty_crypto']
        c_bid = self._agent._df.at[self._agent._df.index[-1], 'bid']
        
        ass_to_xfer = 100/c_bid if c_qty_ass >= 100/c_bid else c_qty_ass
        fee_usd = (ass_to_xfer*c_bid) * self._agent.fee_rate

        n_qty_usd = c_qty_usd + (ass_to_xfer*c_bid) - fee_usd
        n_qty_ass = c_qty_ass - ass_to_xfer

        # Modify the last row in place with the new qty values
        self._agent.update_tail(n_qty_usd, n_qty_ass)
        print(f"{self._agent._clock.get_time()}: ",
            f"{self._agent.__class__.__name__}-{self._agent.fee_rate} SOLD {ass_to_xfer} crypto for {(ass_to_xfer*c_bid) - fee_usd} USD ",
            f"(U: {n_qty_usd}, C: {n_qty_ass}, N: {self._agent._df.at[self._agent._df.index[-1], 'networth']})")
