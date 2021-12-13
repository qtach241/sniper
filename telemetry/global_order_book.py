import sys
import getopt
import logging
import os
import socket
import threading
import json
import time
import datetime as dt
from auth_keys import (api_secret, api_key, api_pass)

import cbpro
import pandas
import btalib

import click
import matplotlib.pyplot as plt

from cbpro_level2_order_book import L2OrderBook

if __name__ == '__main__':
    print("Started global order book at: ", dt.datetime.now())
    
    # Start L2 order books.
    coinbase_btc_usd = L2OrderBook(product_id='BTC-USD')
    coinbase_eth_usd = L2OrderBook(product_id='ETH-USD')
    coinbase_sol_usd = L2OrderBook(product_id='SOL-USD')
    
    coinbase_btc_usd.start()
    coinbase_eth_usd.start()
    coinbase_sol_usd.start()

    # Initial time delay to finish building snapshot
    time.sleep(2)

    while True:
        cb_btc_usd_book = coinbase_btc_usd.export_grouped_snapshot()
        cb_eth_usd_book = coinbase_eth_usd.export_grouped_snapshot()
        cb_sol_usd_book = coinbase_sol_usd.export_grouped_snapshot()

        print(cb_btc_usd_book)
        print(cb_eth_usd_book)
        print(cb_sol_usd_book)

        time.sleep(1)

