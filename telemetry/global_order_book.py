import time
import datetime as dt
import simplejson as json
import pandas
from pymongo import MongoClient
from auth_keys import (api_secret, api_key, api_pass)

from binance_level2_order_book import Bi_L2OrderBook
from cbpro_level2_order_book import Cb_L2OrderBook

import matplotlib.pyplot as plt
from matplotlib import animation

VERSION_STRING = '1.0'

KEY_VERSION = 'v'
KEY_TIMESTAMP = 't'

KEY_EXCHANGE_COINBASE = 'cb'
KEY_EXCHANGE_BINANCE = 'bi'

# The base currency is used to identify the trading pair. The quote
# currency can always be assumed to be USD or equivalent (ie. USDT)
# if it is missing from the pair.
KEY_TRADING_PAIR_BTC_USD = 'BTC'
KEY_TRADING_PAIR_ETH_USD = 'ETH'
KEY_TRADING_PAIR_SOL_USD = 'SOL'
KEY_TRADING_PAIR_MATIC_USD = 'MATIC'

KEY_LAST_UPDATE_AT = 'u'
KEY_BID = 'b'
KEY_ASK = 'a'
KEY_BID_DEPTH = 'bd'
KEY_ASK_DEPTH = 'ad'

if __name__ == '__main__':
    print("Started global order book at: ", dt.datetime.now())

    mongo_client = MongoClient('mongodb://localhost:27017/')
    db = mongo_client['sniper-db']
    collection = db.telemetry
    
    # Start Coinbase L2 order books.
    Coinbase_BTC_USD = Cb_L2OrderBook(product_id='BTC-USD')
    Coinbase_ETH_USD = Cb_L2OrderBook(product_id='ETH-USD')
    Coinbase_SOL_USD = Cb_L2OrderBook(product_id='SOL-USD')
    
    # Layered startup
    print("Subscribing to Coinbase BTC-USD...")
    Coinbase_BTC_USD.create()
    time.sleep(2)

    print("Subscribing to Coinbase ETH-USD...")
    Coinbase_ETH_USD.create()
    time.sleep(2)

    print("Subscribing to Coinbase SOL-USD...")
    Coinbase_SOL_USD.create()
    time.sleep(2)

    # Start Binance L2 order books.
    # NOTE: As of 12/18/21 Binance API truncates initial snapshot. Therefore,
    # these order books are not 100% accurate, but will become more accurate
    # over time.
    Binance_BTC_USDT = Bi_L2OrderBook(symbol='BTCUSDT')
    Binance_ETH_USDT = Bi_L2OrderBook(symbol='ETHUSDT')
    Binance_SOL_USDT = Bi_L2OrderBook(symbol='SOLUSDT')

    # Layered startup
    print("Subscribing to Binance BTCUSDT...")
    Binance_BTC_USDT.create()
    time.sleep(2)

    print("Subscribing to Binance ETHUSDT...")
    Binance_ETH_USDT.create()
    time.sleep(2)

    print("Subscribing to Binance SOLUSDT...")
    Binance_SOL_USDT.create()
    time.sleep(2)

    # Setup data visualizations
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ys = []
    xs = []

    def animate(i, xs, ys):
        # Sample price from order book
        price = Coinbase_SOL_USD.get_mid_market_price()
        
        # Add x and y to lists
        xs.append(dt.datetime.now().strftime('%H:%M:%S'))
        ys.append(price)

        # Limit x and y lists to 100 entries
        xs = xs[-100:]
        ys = ys[-100:]

        # Draw x and y lists
        ax.clear()
        ax.plot(xs, ys)

        # Format plot
        plt.xticks(rotation=45, ha='right')
        plt.subplots_adjust(bottom=0.30)
        plt.title('SOL-USD price over Time')
        plt.ylabel('SOL-USD price')

    #ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=5000)
    #plt.show()

    samples = 0
    while True:

        current_time = dt.datetime.utcnow().isoformat()

        Coinbase_BTC_USD_depth = Coinbase_BTC_USD.export()
        Coinbase_ETH_USD_depth = Coinbase_ETH_USD.export()
        Coinbase_SOL_USD_depth = Coinbase_SOL_USD.export()
        Binance_BTC_USDT_depth = Binance_BTC_USDT.export()
        Binance_ETH_USDT_depth = Binance_ETH_USDT.export()
        Binance_SOL_USDT_depth = Binance_SOL_USDT.export()

        data = {}
        data[KEY_VERSION] = VERSION_STRING
        data[KEY_TIMESTAMP] = current_time
        
        cb_data = {}
        bi_data = {}

        cb_btc_usd_data = {}
        cb_btc_usd_data[KEY_LAST_UPDATE_AT] = Coinbase_BTC_USD.get_update_time()
        cb_btc_usd_data[KEY_BID] = Coinbase_BTC_USD.get_bid()
        cb_btc_usd_data[KEY_ASK] = Coinbase_BTC_USD.get_ask()
        cb_btc_usd_data[KEY_BID_DEPTH] = Coinbase_BTC_USD_depth[1].to_dict()
        cb_btc_usd_data[KEY_ASK_DEPTH] = Coinbase_BTC_USD_depth[0].to_dict()

        cb_eth_usd_data = {}
        cb_eth_usd_data[KEY_LAST_UPDATE_AT] = Coinbase_ETH_USD.get_update_time()
        cb_eth_usd_data[KEY_BID] = Coinbase_ETH_USD.get_bid()
        cb_eth_usd_data[KEY_ASK] = Coinbase_ETH_USD.get_ask()
        cb_eth_usd_data[KEY_BID_DEPTH] = Coinbase_ETH_USD_depth[1].to_dict()
        cb_eth_usd_data[KEY_ASK_DEPTH] = Coinbase_ETH_USD_depth[0].to_dict()

        cb_sol_usd_data = {}
        cb_sol_usd_data[KEY_LAST_UPDATE_AT] = Coinbase_SOL_USD.get_update_time()
        cb_sol_usd_data[KEY_BID] = Coinbase_SOL_USD.get_bid()
        cb_sol_usd_data[KEY_ASK] = Coinbase_SOL_USD.get_ask()
        cb_sol_usd_data[KEY_BID_DEPTH] = Coinbase_SOL_USD_depth[1].to_dict()
        cb_sol_usd_data[KEY_ASK_DEPTH] = Coinbase_SOL_USD_depth[0].to_dict()

        bi_btc_usdt_data = {}
        bi_btc_usdt_data[KEY_LAST_UPDATE_AT] = Binance_BTC_USDT.get_update_time()
        bi_btc_usdt_data[KEY_BID] = Binance_BTC_USDT.get_bid()
        bi_btc_usdt_data[KEY_ASK] = Binance_BTC_USDT.get_ask()
        bi_btc_usdt_data[KEY_BID_DEPTH] = Binance_BTC_USDT_depth[1].to_dict()
        bi_btc_usdt_data[KEY_ASK_DEPTH] = Binance_BTC_USDT_depth[0].to_dict()

        bi_eth_usdt_data = {}
        bi_eth_usdt_data[KEY_LAST_UPDATE_AT] = Binance_ETH_USDT.get_update_time()
        bi_eth_usdt_data[KEY_BID] = Binance_ETH_USDT.get_bid()
        bi_eth_usdt_data[KEY_ASK] = Binance_ETH_USDT.get_ask()
        bi_eth_usdt_data[KEY_BID_DEPTH] = Binance_ETH_USDT_depth[1].to_dict()
        bi_eth_usdt_data[KEY_ASK_DEPTH] = Binance_ETH_USDT_depth[0].to_dict()

        bi_sol_usdt_data = {}
        bi_sol_usdt_data[KEY_LAST_UPDATE_AT] = Binance_SOL_USDT.get_update_time()
        bi_sol_usdt_data[KEY_BID] = Binance_SOL_USDT.get_bid()
        bi_sol_usdt_data[KEY_ASK] = Binance_SOL_USDT.get_ask()
        bi_sol_usdt_data[KEY_BID_DEPTH] = Binance_SOL_USDT_depth[1].to_dict()
        bi_sol_usdt_data[KEY_ASK_DEPTH] = Binance_SOL_USDT_depth[0].to_dict()

        cb_data[KEY_TRADING_PAIR_BTC_USD] = cb_btc_usd_data
        cb_data[KEY_TRADING_PAIR_ETH_USD] = cb_eth_usd_data
        cb_data[KEY_TRADING_PAIR_SOL_USD] = cb_sol_usd_data
        bi_data[KEY_TRADING_PAIR_BTC_USD] = bi_btc_usdt_data
        bi_data[KEY_TRADING_PAIR_ETH_USD] = bi_eth_usdt_data
        bi_data[KEY_TRADING_PAIR_SOL_USD] = bi_sol_usdt_data

        data[KEY_EXCHANGE_COINBASE] = cb_data
        data[KEY_EXCHANGE_BINANCE] = bi_data

        #bids_df = pandas.DataFrame.from_dict(cb_sol_usd_data[KEY_BID_DEPTH])
        #asks_df = pandas.DataFrame.from_dict(cb_sol_usd_data[KEY_ASK_DEPTH])
        #bids_df['size'] = bids_df['size'].apply(pandas.to_numeric)
        #asks_df['size'] = asks_df['size'].apply(pandas.to_numeric)
        #print(bids_df)
        #print(asks_df)

        #json_data = json.dumps(data)
        #print(json_data)

        # Insert into database
        collection.insert_one(data)

        # Increment sample count and display
        samples += 1
        print("Samples Recorded: ", samples, end='\r')

        time.sleep(1)

