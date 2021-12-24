import pandas as pd
from abc import ABC, abstractmethod

from simple_action import Action

DF_COLUMNS = ["unix", "bid", "ask", "qty_usd", "qty_crypto", "networth"]

class Agent(ABC):
    def __init__(self, initial_usd=0, initial_crypto=0) -> None:
        self._initial_usd = initial_usd
        self._initial_crypto = initial_crypto

        self._df = pd.DataFrame(columns=DF_COLUMNS) 
    
    @abstractmethod
    def get_action(self, state) -> Action:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

class HODL_Agent(Agent):
    def __init__(self) -> None:
        super().__init__()
    
    def get_action(self, state) -> Action:
        return super().get_action(state)

    def reset(self) -> None:
        return super().reset()

class DCA_Agent(Agent):
    def __init__(self) -> None:
        super().__init__()
    
    def get_action(self, state) -> Action:
        return super().get_action(state)

    def reset(self) -> None:
        return super().reset()

class DH_Agent(Agent):
    def __init__(self) -> None:
        super().__init__()
    
    def get_action(self, state) -> Action:
        return super().get_action(state)

    def reset(self) -> None:
        return super().reset()

class SmartDCA_Agent(Agent):
    def __init__(self) -> None:
        super().__init__()
    
    def get_action(self, state) -> Action:
        return super().get_action(state)

    def reset(self) -> None:
        return super().reset()
