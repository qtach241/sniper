import sys
import getopt
import logging
import os
import socket
import threading
import time
import pprint
from auth_keys import (api_secret, api_key, api_pass)

import cbpro
import pandas
import btalib

usage_text = "Usage: telemetry.py -e <exchange> -s <symbol>"

symbol = ""
exchange = ""

opts, args =  getopt.getopt(sys.argv[1:], "s:U:u:",["--help"])
for opt, arg in opts:
    if opt == '-e':
        exchange = arg
    elif opt in ("-s"):
        symbool = arg
    elif opt in ("--help"):
        print(usage_text)
        sys.exit()

def thread_loop():
    while True:
        #print("hello from thread!")
        time.sleep(1)

thread = threading.Thread(target=thread_loop, args=())
thread.daemon = True
thread.start()

public_client = cbpro.PublicClient() # Create a public client
print(public_client)

historic_data_columns = ["Date", "Open", "High", "Low", "Close", "Unused"]

historic_data = public_client.get_product_historic_rates("SOL-USD")
dataframe = pandas.DataFrame(historic_data, columns=historic_data_columns)
dataframe["5-Day Moving Average"] = dataframe.Close.rolling(5).mean() # Moving Average via Pandas
dataframe["10-Day Moving Average"] = btalib.sma(dataframe.Close, period=10).df # Moving Average via bta-lib
print(dataframe)

order_book = public_client.get_product_order_book("SOL-USD")
print(order_book)

stats = public_client.get_product_24hr_stats("SOL-USD")
print(stats)

while True:
	ticker = public_client.get_product_ticker(product_id="SOL-USD")
	pprint.pprint(ticker)
	time.sleep(5)

thread.join()
