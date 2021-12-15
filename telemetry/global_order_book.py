import sys
import getopt
import logging
import os
import socket
import threading
import simplejson as json
import time
import datetime as dt
from auth_keys import (api_secret, api_key, api_pass)

import cbpro
import pandas
import btalib

import click
import matplotlib.pyplot as plt

from cbpro_level2_order_book import Cb_L2OrderBook

if __name__ == '__main__':
    print("Started global order book at: ", dt.datetime.now())
    
    # Start Coinbase L2 order books.
    Coinbase_BTC_USD = Cb_L2OrderBook(product_id='BTC-USD')
    Coinbase_ETH_USD = Cb_L2OrderBook(product_id='ETH-USD')
    Coinbase_SOL_USD = Cb_L2OrderBook(product_id='SOL-USD')
    #Coinbase_MAT_USD = Cb_L2OrderBook(product_id='MATIC_USD')
    
    Coinbase_BTC_USD.create()
    Coinbase_ETH_USD.create()
    Coinbase_SOL_USD.create()
    #Coinbase_MAT_USD.create()

    # Initial time delay to finish building snapshot
    time.sleep(5)

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

        #Coinbase_MAT_USD_lut = Coinbase_MAT_USD.get_update_time()
        #Coinbase_MAT_USD_ask = Coinbase_MAT_USD.get_ask()
        #Coinbase_MAT_USD_bid = Coinbase_MAT_USD.get_bid()
        #Coinbase_MAT_USD_depth = Coinbase_MAT_USD.export()

        data = {}
        data['timestamp'] = current_time
        
        cb_data = {}

        cb_btc_usd_data = {}
        cb_btc_usd_data['last_update_at'] = Coinbase_BTC_USD_lut
        cb_btc_usd_data['bid'] = Coinbase_BTC_USD_bid
        cb_btc_usd_data['ask'] = Coinbase_BTC_USD_ask
        cb_btc_usd_data['bid_depth'] = Coinbase_BTC_USD_depth[1].to_dict()
        cb_btc_usd_data['ask_depth'] = Coinbase_BTC_USD_depth[0].to_dict()

        cb_eth_usd_data = {}
        cb_eth_usd_data['last_update_at'] = Coinbase_ETH_USD_lut
        cb_eth_usd_data['bid'] = Coinbase_ETH_USD_bid
        cb_eth_usd_data['ask'] = Coinbase_ETH_USD_ask
        cb_eth_usd_data['bid_depth'] = Coinbase_ETH_USD_depth[1].to_dict()
        cb_eth_usd_data['ask_depth'] = Coinbase_ETH_USD_depth[0].to_dict()

        cb_sol_usd_data = {}
        cb_sol_usd_data['last_update_at'] = Coinbase_SOL_USD_lut
        cb_sol_usd_data['bid'] = Coinbase_SOL_USD_bid
        cb_sol_usd_data['ask'] = Coinbase_SOL_USD_ask
        cb_sol_usd_data['bid_depth'] = Coinbase_SOL_USD_depth[1].to_dict()
        cb_sol_usd_data['ask_depth'] = Coinbase_SOL_USD_depth[0].to_dict()

        #cb_mat_usd_data = {}
        #cb_mat_usd_data['last_update_at'] = Coinbase_MAT_USD_lut
        #cb_mat_usd_data['bid'] = Coinbase_MAT_USD_bid
        #cb_mat_usd_data['ask'] = Coinbase_MAT_USD_ask
        #cb_mat_usd_data['bid_depth'] = Coinbase_MAT_USD_depth[1].to_dict()
        #cb_mat_usd_data['ask_depth'] = Coinbase_MAT_USD_depth[0].to_dict()

        cb_data['BTC-USD'] = cb_btc_usd_data
        cb_data['ETH-USD'] = cb_eth_usd_data
        cb_data['SOL-USD'] = cb_sol_usd_data
        #cb_data['MATIC-USD'] = cb_mat_usd_data

        data['coinbase'] = cb_data

        bids_df = pandas.DataFrame.from_dict(cb_sol_usd_data['bid_depth'])
        asks_df = pandas.DataFrame.from_dict(cb_sol_usd_data['ask_depth'])
        print(bids_df)
        print(asks_df)

        json_data = json.dumps(data)
        print(json_data)

        time.sleep(1)

