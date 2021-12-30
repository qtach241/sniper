from abc import ABC, abstractmethod
from clock import Clock
from simple_agent import Agent, DCA_Agent, DH_Agent, HODL_Agent, SmartDCA_Agent
from simple_observer import Observer, CsvObserver, WebApiObserver, TelemetryObserver

import cbpro
import pandas as pd
import datetime as dt
import math
import time

DO_INIT_LOOPS = 96 # Number of API calls needed to back-populate 20 days initial dataframe. (28800 / 300)
SECONDS_PER_LOOP = 60*300 # 60 seconds per minute, 300 minutes per API call

SECONDS_PER_DAY = 86400
SECONDS_PER_20DAYS = SECONDS_PER_DAY*20

SIMULATED_SPREAD = 0.03

class Environment(ABC):
    """
    The environment is the main module of the simple strategies system. It
    encapsulates the observer and agent classes. The environment initializes
    the clock, the observer with observation parameters, and the agent(s) with
    the initial dataframe. Once the system is initialized, the environment
    controls program flow by repeated calls to the step() function.

    The primary objective of the environment is to provide the initial data
    (back-populated dataframe) to agents. This occurs during the initialization
    stage. Once initialized, the environment observes new data, presents new
    data to agents, and records / executes actions from agents.

    The step() function retreives the next "observation" from the observer in
    the form of a single line dataframe. This is then passed to each agent
    via the agent's update() function. The individual agents are responsible
    for populating additional dataframe columns as needed. Once updated, the
    environment invokes and executes the action of each agent. This process
    continues until the stop condition (if any) is reached.
    """
    def __init__(self, time) -> None:
        self._clock = Clock(time)

    @abstractmethod
    def step(self) -> None:
        pass

class LiveEnvironment(Environment):
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

class SimulatedEnvironment(Environment):
    """
    Environments can be one of two types: Live or Simulated.

    A simulated environment, unlike the live environment, can support multiple
    agents. Agents operating in a simulated environment will not interact with a
    live API. As such, only a partial state is observed. The environment simulates
    the actions selected by the agent and "fills in" the rest of the state.

    Simulated evironments, if used with the CsvObserver must be initialized with
    a start time and an end time to define at what point in history to start the
    CSV play back from and what timestamp to end play back, and thus the simulation.

    If used with either real-time MongoDB or WebAPI observers, the start_time is
    automatically assumed to be the current time.

    The epoch_period parameter defines the time period in days for each "epoch".
    Performance of agents is evaluated over several time slices which include the
    epoch period.
    """
    def __init__(self, start_time=0, end_time=0, epoch_period=3):
        super().__init__(time=start_time)
        self._start_time = start_time # Unix format (seconds)
        self._end_time = end_time # Unix format (seconds)
        self._epoch_period = epoch_period # Epoch period in days
        
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

    def initialize_agents(self, id, qty_usd, qty_crypto):
        # To back-populate dataframe, use public API client to query historic candle data from
        # start time backwards to the limit time (set to 20 days).
        public_client = cbpro.PublicClient()
        loop_datetime = self._start_time
        loop_limit_datetime = loop_datetime - SECONDS_PER_20DAYS
        candles = []
        while loop_datetime >= loop_limit_datetime:
            candles += public_client.get_product_historic_rates(product_id=id,
                start=dt.datetime.utcfromtimestamp(loop_datetime - SECONDS_PER_LOOP).isoformat(),
                end=dt.datetime.utcfromtimestamp(loop_datetime).isoformat(),
                granularity=60)
            loop_datetime -= SECONDS_PER_LOOP
            # Short delay to prevent API throttle
            time.sleep(0.2)
        
        # Now that candles has all the data in the desired timeframe, convert the list to a
        # dataframe that agents can use.
        df = pd.DataFrame(candles, columns=['unix', 'low', 'high', 'open', 'close', 'volume'])
        # Sort dataframe by ascending (earlier timestamps appear first or top)
        df.sort_values(by=['unix'], inplace=True, ascending=True)
        
        # Add new derived columns used by agents
        df['bid'] = df['close'] - SIMULATED_SPREAD/2
        df['ask'] = df['close'] + SIMULATED_SPREAD/2
        df['qty_usd'] = qty_usd
        df['qty_crypto'] = qty_crypto
        df['networth'] = (df['bid'] * qty_crypto) + qty_usd

        # Drop columns that aren't used by any agents
        df.drop(columns=['low', 'high', 'open', 'close', 'volume'], inplace=True)

        # Update agent's dateframe
        for agent in self._agents:
            agent.update(df)

        #data["5-Day Moving Average"] = data['close'].rolling(7200).mean() # Moving Average via Pandas
        #df.to_csv(f'init_data.csv', index=False, header=True)

    def step(self):
        # Get latest dataframe from observer.
        observation = self._obs.observe()

        # Update clock with the latest unix timestamp (new obs should only contain 1 row)
        self._clock.set_time(observation.iloc[-1]['unix'])

        # Additional feature processing
        #columns = ["unix", "bid", "ask", "qty_usd", "qty_crypto", "networth"]

        #df = pandas.DataFrame(historic_data, columns=historic_data_columns)
        #dataframe["5-Day Moving Average"] = dataframe.Close.rolling(5).mean() # Moving Average via Pandas
        #dataframe["10-Day Moving Average"] = btalib.sma(dataframe.Close, period=10).df # Moving Average via bta-lib

        for agent in self._agents:
            agent.update(observation)
            #action = agent.get_action()
            #action.simulate()
            agent.get_action().simulate()

        # Simulate the action

    def run_to_completion(self):
        pass

    def run(self):
        pass

if __name__ == '__main__':
    # The start time must be retrieved using datetime.now(), conversion to UTC occurs in initialize_agents().
    #start_time = math.floor(dt.datetime.now().timestamp())
    start_time = 1630689360-1
    end_time = 5000000000 # Basically never end
    print(f"Simulated Environment started with unix time: {start_time}")
    
    env = SimulatedEnvironment(start_time=start_time, end_time=end_time, epoch_period=7)
    obs = CsvObserver(filepath='csv/Coinbase_SOLUSD_data_sorted.csv', offset_minutes=0, spread=SIMULATED_SPREAD)

    env.load_observer(obs)

    agents = [
        HODL_Agent(),
        #DCA_Agent(),
        #DH_Agent(),
        #SmartDCA_Agent(),
    ]
    
    env.load_agents(agents)

    env.initialize_agents(id='SOL-USD', qty_usd=1000, qty_crypto=10)

    for x in range(6):
        env.step()
