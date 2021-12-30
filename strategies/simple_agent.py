import pandas as pd
from abc import ABC, abstractmethod

from simple_action import Action, Action_Hold, Action_BuyAll

DF_COLUMNS = ["unix", "bid", "ask", "qty_usd", "qty_crypto", "networth"]

class Agent(ABC):
    def __init__(self, initial_usd=0, initial_crypto=0) -> None:
        self._initial_usd = initial_usd
        self._initial_crypto = initial_crypto

        self._df = pd.DataFrame(columns=DF_COLUMNS)

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
    def __init__(self) -> None:
        super().__init__()
    
    def get_action(self) -> Action:
        last_qty_usd = self._df.iloc[-1]['qty_usd']
        if last_qty_usd > 0:
            return Action_BuyAll(agent=self)
        else:
            return Action_Hold(agent=self)

    def reset(self) -> None:
        return super().reset()

class DCA_Agent(Agent):
    def __init__(self) -> None:
        super().__init__()
    
    def get_action(self) -> Action:
        pass

    def reset(self) -> None:
        return super().reset()

class DH_Agent(Agent):
    def __init__(self) -> None:
        super().__init__()
    
    def get_action(self) -> Action:
        pass

    def reset(self) -> None:
        return super().reset()

class SmartDCA_Agent(Agent):
    def __init__(self) -> None:
        super().__init__()
    
    def get_action(self) -> Action:
        pass

    def reset(self) -> None:
        return super().reset()