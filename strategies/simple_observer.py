from abc import ABC, abstractmethod
from pymongo import MongoClient
import datetime as dt
import pandas as pd
import math
import json
import cbpro
import os

API_SECRET = 'yIQzb6aYGoWK6e1fyql5OAhWoQZoJRjEUVLZ3VjHnf9hvtvC9+KosCDy6Z9W48XnVSfpsdQlKlgDVhuIJlpTyA=='
API_KEY = '82105147c85ee283769f28bd0fd398dc'
API_PASS = 'tmi2htht53b'

DF_COLUMNS = ["unix", "bid", "ask", "qty_usd", "qty_crypto", "networth"]

DEFAULT_SYMBOL = 'SOL'

class Observer(ABC):
    def __init__(self, symbol=DEFAULT_SYMBOL) -> None:
        self._symbol = symbol

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def product_id(self) -> str:
        return self._symbol + "-USD" # Coinbase format
    
    @abstractmethod
    def observe(self) -> pd.DataFrame:
        pass

class CsvObserver(Observer):
    """
    The CSV Observer reads a CSV file containing historic candle data for a
    particular asset. The CSV is expected to generated and prepared before hand
    using the data_util.py script and sorted in ascending order via sort_data.py.
    
    This type of observer is used for testing agents with recorded data at rest.
    By rapidly stepping through observations, we're able to quickly replay data
    in various timeframes to evaluate an agent's performance over time.
    """
    def __init__(self, symbol=None, filepath='', offset_minutes=0, spread=0):
        super().__init__(symbol=symbol)

        self._dir = os.path.dirname(__file__)
        self._filepath = os.path.join(self._dir, filepath)
        
        self._offset_minutes = offset_minutes
        self._spread = spread # Simulated

        self._obs_generator = self._get_obs_generator()

    def _get_obs_generator(self):
        with pd.read_csv(self._filepath, chunksize=1, header=None, skiprows=self._offset_minutes) as reader:
            for chunk in reader:
                yield chunk

    def observe(self):
        # Read the next candle from the CSV file formatted to a dataframe.
        df = next(self._obs_generator)
        # Format the data into a new dataframe to represent the observed state.
        return pd.DataFrame({
            'unix': df.iloc[0][0], 
            'bid': df.iloc[0][4] - self._spread, 
            'ask': df.iloc[0][4] + self._spread, 
            'qty_usd': None, 
            'qty_crypto': None, 
            'networth': None
            }, columns=DF_COLUMNS, index=[0])

class WebApiObserver(Observer):
    """
    The WebApi Observer queries real-time ticker and wallet data from the
    Coinbase REST API. Since the data is polled from live endpoints, this
    observer is not suitable for rapid testing of agents and is used for
    running an agent in the live environment.
    """
    def __init__(self, symbol=DEFAULT_SYMBOL):
        super().__init__(symbol=symbol)
        
        self._auth_client = cbpro.AuthenticatedClient(API_KEY, API_SECRET, API_PASS)
        self._qty_usd = None
        self._qty_crypto = None

    def observe(self):
        # Fetch ticker data on-demand via REST API.
        ticker = self._auth_client.get_product_ticker(product_id=self.product_id)
        # Fetch wallet state on-demand via REST API.
        accounts = self._auth_client.get_accounts()
        for account in accounts:
            if account['currency'] == 'USD':
                self._qty_usd = float(account['balance'])
            elif account['currency'] == self.symbol:
                self._qty_crypto = float(account['balance'])

        dtf = dt.datetime.fromisoformat(ticker['time'][:-1])
        return pd.DataFrame({
            'unix': math.floor(dtf.timestamp()),
            'bid': float(ticker['bid']),
            'ask': float(ticker['ask']),
            'qty_usd': self._qty_usd,
            'qty_crypto': self._qty_crypto,
            'networth': self._qty_crypto*float(ticker['bid']) + self._qty_usd
            }, columns=DF_COLUMNS, index=[0])

class TelemetryObserver(Observer):
    """
    The Telemetry Observer reads ticker data from the telemetry Mongo DB
    collection and wallet data from the Coinbase REST API. Telemetry data
    stored in the Mongo DB collection has second precision unlike the Web 
    API Observer.
    """
    def __init__(self, symbol=DEFAULT_SYMBOL, url='mongodb://localhost:27017/', db='sniper-db', collection='telemetry'):
        super().__init__(symbol=symbol)
        
        self._mongo_client = MongoClient(url)
        self._db = self._mongo_client[db]
        self._collection = self._db[collection]

        self._auth_client = cbpro.AuthenticatedClient(API_KEY, API_SECRET, API_PASS)
        self._qty_usd = None
        self._qty_crypto = None

    def observe(self):
        # Fetch ticker data from last entry stored in Mongo DB collection.
        cursor = self._collection.find().sort("_id", -1).limit(1)
        # Fetch wallet state on-demand via REST API.
        accounts = self._auth_client.get_accounts()
        for account in accounts:
            if account['currency'] == 'USD':
                self._qty_usd = float(account['balance'])
            elif account['currency'] == self.symbol:
                self._qty_crypto = float(account['balance'])

        dtf = cursor[0]['t']
        return pd.DataFrame({
            'unix': math.floor(dtf.timestamp()), 
            'bid': cursor[0]['cb']['SOL']['b'], 
            'ask': cursor[0]['cb']['SOL']['a'], 
            'qty_usd': self._qty_usd, 
            'qty_crypto': self._qty_crypto, 
            'networth': self._qty_crypto*cursor[0]['cb']['SOL']['b'] + self._qty_usd
            }, columns=DF_COLUMNS, index=[0])

if __name__ == '__main__':
    print("Test CsvObserver:")
    csv_obs = CsvObserver(filepath='csv/Coinbase_SOLUSD_data_sorted.csv', offset_minutes=0, spread=0.03)
    for x in range(1, 6):
        csv_obs_ret = csv_obs.observe()
        print(csv_obs_ret)

    print("Test WebApiObserver:")
    web_obs = WebApiObserver(symbol='SOL')
    web_obs_ret = web_obs.observe()
    print(web_obs_ret)

    print("Test TelemetryObserver:")
    db_obs = TelemetryObserver()
    db_obs_ret = db_obs.observe()
    print(db_obs_ret)
