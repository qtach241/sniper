from abc import ABC, abstractmethod
from clock import Clock
from simple_agent import Agent, DCA_Agent, DH_Agent, HODL_Agent, SmartDCA_Agent
from simple_observer import Observer, CsvObserver, WebApiObserver, LiveMongoDbObserver

import pandas as pd

class Environment(ABC):
    def __init__(self) -> None:
        self._clock = Clock()

    @abstractmethod
    def step(self) -> None:
        pass

class LiveEnvironment():
    """
    Environments can be one of two types: Live or Simulated.

    A live environment, unlike simulated environments, can only support a single
    agent as that agent's actions will interact with the live API. The live
    environment observes the full state from the source and will not "fill in"
    fields such as "qty_usd", "qty_crypto", or "networth".
    """
    def __init__(self) -> None:
        self._obs = None
        self._agent = None

    def load_observer(self, obs):
        if (isinstance(obs, WebApiObserver)):
            self._obs = obs
        else:
            print("ERROR: LiveEnvironment only supports WebApiObserver.")

    def load_agent(self, agent):
        pass

    def step(self):
        pass

class SimulatedEnvironment():
    """
    Environments can be one of two types: Live or Simulated.

    A simulated environment, unlike the live environmentt, can support multiple
    agents. Agents operating in a simulated environment will not interact with a
    live API. As such, only a partial state is observed. The environment simulates
    the actions selected by the agent and "fills in" the rest of the state.
    """
    def __init__(self, start_date=0, epoch_days=3):
        self._obs = None
        self._agents = []

    def load_observer(self, obs):
        if (isinstance(obs, Observer)):
            self._obs = obs
        else:
            print("ERROR: Cannot load object not of type Observer.")

    def load_agents(self, agents):
        for agent in agents:
            if (isinstance(agent, Agent)):
                self._agents.append(agent)
            else:
                print("ERROR: Cannot load object not of type Agent!")

    def step(self):
        observation = self._obs.observe()

        # Additional feature processing
        columns = ["unix", "bid", "ask", "qty_usd", "qty_crypto", "networth"]

        #df = pandas.DataFrame(historic_data, columns=historic_data_columns)
        #dataframe["5-Day Moving Average"] = dataframe.Close.rolling(5).mean() # Moving Average via Pandas
        #dataframe["10-Day Moving Average"] = btalib.sma(dataframe.Close, period=10).df # Moving Average via bta-lib

        for agent in self._agents:
            action = agent.get_action(observation)
            action.simulate()

        # Simulate the action

    def run_to_completion(self):
        pass


if __name__ == '__main__':
    env = SimulatedEnvironment()
    obs = CsvObserver(filepath='csv/Coinbase_SOLUSD_data_sorted.csv', offset_minutes=0)

    env.load_observer(obs)

    agents = [
        HODL_Agent(),
        DCA_Agent(),
        DH_Agent(),
        SmartDCA_Agent(),
    ]

    for agent in agents:
        if (isinstance(agent, Agent)):
            print("good")
    
    env.load_agents(agents)



