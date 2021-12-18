import time
import datetime as dt
import simplejson as json
import pandas
from auth_keys import (api_secret, api_key, api_pass)

from binance_level2_order_book import Bi_L2OrderBook
from cbpro_level2_order_book import Cb_L2OrderBook

import matplotlib.pyplot as plt
from matplotlib import animation

KEY_TIMESTAMP = 't'

KEY_EXCHANGE_COINBASE = 'cb'
KEY_EXCHANGE_BINANCE = 'bi'

# Different exchanges use different symbol / product formats, ie
# Coinbase uses 'BTC-USD', while Binanace uses 'BTCUSD'. The key used
# to represent and store trading pairs will use a 'btcusd' format.
KEY_TRADING_PAIR_BTC_USD = 'btcusd'
KEY_TRADING_PAIR_ETH_USD = 'ethusd'
KEY_TRADING_PAIR_SOL_USD = 'solusd'
KEY_TRADING_PAIR_MATIC_USD = 'maticusd'

KEY_LAST_UPDATE_AT = 't'
KEY_BID = 'b'
KEY_ASK = 'a'
KEY_BID_DEPTH = 'bd'
KEY_ASK_DEPTH = 'ad'

if __name__ == '__main__':
    print("Started global order book at: ", dt.datetime.now())
    
    # Start Coinbase L2 order books.
    Coinbase_BTC_USD = Cb_L2OrderBook(product_id='BTC-USD')
    Coinbase_ETH_USD = Cb_L2OrderBook(product_id='ETH-USD')
    Coinbase_SOL_USD = Cb_L2OrderBook(product_id='SOL-USD')
    Coinbase_MAT_USD = Cb_L2OrderBook(product_id='MATIC-USD')
    
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

    print("Subscribing to Coinbase MATIC-USD...")
    Coinbase_MAT_USD.create()
    time.sleep(2)

    # Start Binance L2 order books.
    Binance_SOL_USDT = Bi_L2OrderBook(symbol='SOLUSDT')
    
    # Layered startup
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

    while True:

        current_time = dt.datetime.utcnow().isoformat()

        Coinbase_BTC_USD_lut = Coinbase_BTC_USD.get_update_time()
        Coinbase_BTC_USD_ask = Coinbase_BTC_USD.get_ask()
        Coinbase_BTC_USD_bid = Coinbase_BTC_USD.get_bid()
        Coinbase_BTC_USD_depth = Coinbase_BTC_USD.export()

        Coinbase_ETH_USD_lut = Coinbase_ETH_USD.get_update_time()
        Coinbase_ETH_USD_ask = Coinbase_ETH_USD.get_ask()
        Coinbase_ETH_USD_bid = Coinbase_ETH_USD.get_bid()
        Coinbase_ETH_USD_depth = Coinbase_ETH_USD.export()

        Coinbase_SOL_USD_lut = Coinbase_SOL_USD.get_update_time()
        Coinbase_SOL_USD_ask = Coinbase_SOL_USD.get_ask()
        Coinbase_SOL_USD_bid = Coinbase_SOL_USD.get_bid()
        Coinbase_SOL_USD_depth = Coinbase_SOL_USD.export()

        Coinbase_MAT_USD_lut = Coinbase_MAT_USD.get_update_time()
        Coinbase_MAT_USD_ask = Coinbase_MAT_USD.get_ask()
        Coinbase_MAT_USD_bid = Coinbase_MAT_USD.get_bid()
        Coinbase_MAT_USD_depth = Coinbase_MAT_USD.export()

        Binance_SOL_USDT_lut = Binance_SOL_USDT.get_update_time()
        Binance_SOL_USDT_ask = Binance_SOL_USDT.get_ask()
        Binance_SOL_USDT_bid = Binance_SOL_USDT.get_bid()
        Binance_SOL_USDT_depth = Binance_SOL_USDT.export()

        data = {}
        data[KEY_TIMESTAMP] = current_time
        
        cb_data = {}
        bi_data = {}

        cb_btc_usd_data = {}
        cb_btc_usd_data[KEY_LAST_UPDATE_AT] = Coinbase_BTC_USD_lut
        cb_btc_usd_data[KEY_BID] = Coinbase_BTC_USD_bid
        cb_btc_usd_data[KEY_ASK] = Coinbase_BTC_USD_ask
        cb_btc_usd_data[KEY_BID_DEPTH] = Coinbase_BTC_USD_depth[1].to_dict()
        cb_btc_usd_data[KEY_ASK_DEPTH] = Coinbase_BTC_USD_depth[0].to_dict()

        cb_eth_usd_data = {}
        cb_eth_usd_data[KEY_LAST_UPDATE_AT] = Coinbase_ETH_USD_lut
        cb_eth_usd_data[KEY_BID] = Coinbase_ETH_USD_bid
        cb_eth_usd_data[KEY_ASK] = Coinbase_ETH_USD_ask
        cb_eth_usd_data[KEY_BID_DEPTH] = Coinbase_ETH_USD_depth[1].to_dict()
        cb_eth_usd_data[KEY_ASK_DEPTH] = Coinbase_ETH_USD_depth[0].to_dict()

        cb_sol_usd_data = {}
        cb_sol_usd_data[KEY_LAST_UPDATE_AT] = Coinbase_SOL_USD_lut
        cb_sol_usd_data[KEY_BID] = Coinbase_SOL_USD_bid
        cb_sol_usd_data[KEY_ASK] = Coinbase_SOL_USD_ask
        cb_sol_usd_data[KEY_BID_DEPTH] = Coinbase_SOL_USD_depth[1].to_dict()
        cb_sol_usd_data[KEY_ASK_DEPTH] = Coinbase_SOL_USD_depth[0].to_dict()

        cb_mat_usd_data = {}
        cb_mat_usd_data[KEY_LAST_UPDATE_AT] = Coinbase_MAT_USD_lut
        cb_mat_usd_data[KEY_BID] = Coinbase_MAT_USD_bid
        cb_mat_usd_data[KEY_ASK] = Coinbase_MAT_USD_ask
        cb_mat_usd_data[KEY_BID_DEPTH] = Coinbase_MAT_USD_depth[1].to_dict()
        cb_mat_usd_data[KEY_ASK_DEPTH] = Coinbase_MAT_USD_depth[0].to_dict()

        bi_sol_usdt_data = {}
        bi_sol_usdt_data[KEY_LAST_UPDATE_AT] = Binance_SOL_USDT_lut
        bi_sol_usdt_data[KEY_BID] = Binance_SOL_USDT_bid
        bi_sol_usdt_data[KEY_ASK] = Binance_SOL_USDT_ask
        bi_sol_usdt_data[KEY_BID_DEPTH] = Binance_SOL_USDT_depth[1].to_dict()
        bi_sol_usdt_data[KEY_ASK_DEPTH] = Binance_SOL_USDT_depth[0].to_dict()

        cb_data[KEY_TRADING_PAIR_BTC_USD] = cb_btc_usd_data
        cb_data[KEY_TRADING_PAIR_ETH_USD] = cb_eth_usd_data
        cb_data[KEY_TRADING_PAIR_SOL_USD] = cb_sol_usd_data
        cb_data[KEY_TRADING_PAIR_MATIC_USD] = cb_mat_usd_data
        bi_data[KEY_TRADING_PAIR_SOL_USD] = bi_sol_usdt_data

        data[KEY_EXCHANGE_COINBASE] = cb_data
        data[KEY_EXCHANGE_BINANCE] = bi_data

        #bids_df = pandas.DataFrame.from_dict(cb_sol_usd_data[KEY_BID_DEPTH])
        #asks_df = pandas.DataFrame.from_dict(cb_sol_usd_data[KEY_ASK_DEPTH])
        #bids_df['size'] = bids_df['size'].apply(pandas.to_numeric)
        #asks_df['size'] = asks_df['size'].apply(pandas.to_numeric)
        #print(bids_df)
        #print(asks_df)

        json_data = json.dumps(data)
        print(json_data)

        time.sleep(1)

