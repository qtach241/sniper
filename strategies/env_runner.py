import click
import time
from simple_env import SimulatedEnvironment
from simple_observer import CsvObserver
from simple_agent import Agent, HODL_Agent, DCA_Benchmark_Agent, Test_Agent, SMA_5_20_Agent, SMA_1_5_Agent, DCA_Agent, RSI_Agent, RSI_MACD_Agent

SIMULATED_SPREAD = 0.03

CBPRO_FEE_RATE = 0.005
BINANCE_FEE_RATE = 0.001

@click.group()
def runner():
    """A simple CLI for running simple strategy environments."""
    pass

@runner.command()
@click.option('--symbol', prompt='Enter Symbol', help='Symbol (ie. BTC/USD)')
def sim(symbol):
    """
    Simulate various agents under a test environment.
    """
    # The start time must be retrieved using datetime.now(), conversion to UTC occurs in initialize_agents().
    #start_time = math.floor(dt.datetime.now().timestamp())
    start_time = 1630689360-1
    #end_time = 5000000000 # Basically never end
    end_time = 1640153700
    print(f"Simulated Environment started with unix time: {start_time}")
    
    env = SimulatedEnvironment(start_time=start_time, end_time=end_time, epoch_period=7)
    obs = CsvObserver(filepath='csv/Coinbase_SOLUSD_data_sorted.csv', offset_minutes=0, spread=SIMULATED_SPREAD)

    env.load_observer(obs)

    agents = [
        DCA_Benchmark_Agent(fee=CBPRO_FEE_RATE, cd_days=3, qty=1000),
        RSI_MACD_Agent(fee=CBPRO_FEE_RATE, cd_days=0, qty=1000, length=10, fast=1920, slow=5040, signal=1200)
    ]
    
    env.load_agents(agents)

    env.initialize_agents(id='SOL-USD', qty_usd=1000000, qty_crypto=0)

    exec_start = time.time()
    env.run()
    print(f"Environment run completed in: {time.time() - exec_start} seconds!")

    for agent in agents:
        print(f"Final cost basis {agent.__class__.__name__}: {agent.get_cost_basis()}")

if __name__ == '__main__':
    runner()
