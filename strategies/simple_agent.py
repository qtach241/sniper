import pandas as pd
from abc import ABC, abstractmethod

from simple_action import Action, Action_Hold, Action_BuyAll

DF_COLUMNS = ["unix", "bid", "ask", "qty_usd", "qty_crypto", "networth"]

class Agent(ABC):
    def __init__(self, initial_usd=0, initial_crypto=0) -> None:
        self._initial_usd = initial_usd
        self._initial_crypto = initial_crypto

        self._df = pd.DataFrame(columns=DF_COLUMNS)

    @abstractmethod
    def update(self, df) -> None:
        self._df = self._df.append(df, ignore_index=True)
    
    @abstractmethod
    def get_action(self) -> Action:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

class HODL_Agent(Agent):
    def __init__(self) -> None:
        super().__init__()

    def update(self, df) -> None:
        super().update(df)
    
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
