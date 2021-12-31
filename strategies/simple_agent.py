import pandas as pd
from abc import ABC, abstractmethod

from simple_action import Action, Action_Hold, Action_BuyAll, Action_Buy100, Action_Sell100

CD_NONE = 0
CD_ONE_HOUR = 3600
CD_SIX_HOUR = 21600
CD_ONE_DAY = 86400

DF_COLUMNS = ["unix", "bid", "ask", "qty_usd", "qty_crypto", "networth"]

class Agent(ABC):
    def __init__(self, fee=0) -> None:
        self._df = pd.DataFrame(columns=DF_COLUMNS)
        self._clock = None
        self._action_list = []
        self._fee = fee

    @property
    def fee_rate(self):
        return self._fee

    def set_clock(self, obj) -> None:
        self._clock = obj

    def set_action_list(self, action_list) -> None:
        self._action_list = action_list

    def update(self, df, qty_usd=None, qty_crypto=None) -> None:
        self._df = self._df.append(df, ignore_index=True)

        if qty_usd == None or qty_crypto == None:
            # If qty_usd or qty_crypto is not specified, then we either expect the dataframe
            # to be a fully complete dataframe (from a live observer) or a partially complete
            # dataframe from a play-back (ie. csv) observer, in which we'll need to "fill in"
            # the missing NaN cells.
            if pd.isna(self._df.iloc[-1]['qty_usd']):
                self._df.at[self._df.index[-1],'qty_usd'] = self._df.iloc[-2]['qty_usd']
            if pd.isna(self._df.iloc[-1]['qty_crypto']):
                self._df.at[self._df.index[-1],'qty_crypto'] = self._df.iloc[-2]['qty_crypto']
            if pd.isna(self._df.iloc[-1]['networth']):
                self._df.at[self._df.index[-1],'networth'] = self._df.iloc[-1]['qty_usd'] + (self._df.iloc[-1]['qty_crypto']*self._df.iloc[-1]['bid'])
        else:
            # If BOTH qty_usd and qty_crypto are specified, then we are simulating these cells
            # instead of fetching live data from the observer.
            self.update_tail(qty_usd, qty_crypto)

    def update_tail(self, qty_usd, qty_crypto) -> None:
        self._df.at[self._df.index[-1], 'qty_usd'] = qty_usd
        self._df.at[self._df.index[-1], 'qty_crypto'] = qty_crypto
        self._df.at[self._df.index[-1], 'networth'] = qty_usd + (qty_crypto*self._df.iloc[-1]['bid'])
    
    def reset(self) -> None:
        pass
    
    @abstractmethod
    def get_action(self) -> Action:
        pass

class HODL_Agent(Agent):
    def __init__(self, fee=0) -> None:
        super().__init__(fee)
        action_list = [
            Action_Hold(agent=self, cd=CD_NONE),
            Action_BuyAll(agent=self, cd=CD_SIX_HOUR)
        ]
        self.set_action_list(action_list)
    
    def get_action(self) -> Action:
        last_qty_usd = self._df.iloc[-1]['qty_usd']
        if last_qty_usd > 0:
            return self._action_list[1] # Buy All
        else:
            return self._action_list[0] # Hold

    def reset(self) -> None:
        return super().reset()

class Test_Agent(Agent):
    def __init__(self, fee=0) -> None:
        super().__init__(fee)
        action_list = [
            Action_Hold(agent=self, cd=CD_NONE),
            Action_Buy100(agent=self, cd=CD_SIX_HOUR),
            Action_Sell100(agent=self, cd=CD_SIX_HOUR)
        ]
        self.set_action_list(action_list)
    
    def get_action(self) -> Action:
        bid = self._df.iloc[-1]['bid']
        ask = self._df.iloc[-1]['ask']
        last_qty_usd = self._df.iloc[-1]['qty_usd']
        last_qty_ass = self._df.iloc[-1]['qty_crypto']
        if ask < 160 and last_qty_usd > 0:
            return self._action_list[1] # Buy 100
        elif bid > 200 and last_qty_ass > 0:
            return self._action_list[2] # Sell 100
        else:
            return self._action_list[0] # Hold

    def reset(self) -> None:
        return super().reset()

class Bollinger_Agent(Agent):
    def __init__(self, fee) -> None:
        super().__init__(fee)
        action_list = [
            Action_Hold(agent=self, cd=CD_NONE),
            Action_Buy100(agent=self, cd=CD_SIX_HOUR),
            Action_Sell100(agent=self, cd=CD_SIX_HOUR)
        ]
        self.set_action_list(action_list)

    def get_action(self) -> Action:
        pass
