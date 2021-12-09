import sys
import getopt
import logging
import os
import socket
import threading
import time
import pprint
import json
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

class CbproWsClient(cbpro.WebsocketClient):
    def on_open(self):
        #self.url = "wss://ws-feed-public.sandbox.exchange.coinbase.com"
        self.url = "wss://ws-feed.pro.coinbase.com/"
        #self.url = "wss://ws-feed.exchange.coinbase.com"
        #self.products = ["BTC-USD"]
        #self.channels = ["ticker"]
        self.message_count = 0
        print("Let's count the messages!")

    def on_message(self, msg):
        print(json.dumps(msg, indent=4, sort_keys=True))
        self.message_count += 1
        msg_type = msg.get('type', None)
        print("msg_type: ", msg_type, self.message_count)

    def on_close(self):
        print("-- Goodbye! --")
        sys.exit(0)

def thread_loop():
    while True:
        #print("hello from thread!")
        time.sleep(1)

thread = threading.Thread(target=thread_loop, args=())
thread.daemon = True
thread.start()

wsClient = CbproWsClient(products=['SOL-USD'], channels=['level2'])
wsClient.start()
print(wsClient.url, wsClient.products)

public_client = cbpro.PublicClient() # Create a public client
#print(public_client)

all_products = public_client.get_products()
#pprint.pprint(all_products)

historic_data_columns = ["Date", "Open", "High", "Low", "Close", "Unused"]

historic_data = public_client.get_product_historic_rates("SOL-USD")
dataframe = pandas.DataFrame(historic_data, columns=historic_data_columns)
dataframe["5-Day Moving Average"] = dataframe.Close.rolling(5).mean() # Moving Average via Pandas
dataframe["10-Day Moving Average"] = btalib.sma(dataframe.Close, period=10).df # Moving Average via bta-lib
#print(dataframe)

#order_book = public_client.get_product_order_book("SOL-USD", level=3)
#pprint.pprint(order_book)

stats = public_client.get_product_24hr_stats("SOL-USD")
#print(stats)

try:
    while True:
        #ticker = public_client.get_product_ticker(product_id="SOL-USD")
        #pprint.pprint(ticker)
        #time.sleep(5)
        #print("\nMessageCount =", "%i \n" % wsClient.message_count)
        time.sleep(1)
except KeyboardInterrupt:
    wsClient.close()

#if wsClient.error:
    #sys.exit(1)
#else:
    #sys.exit(0)

#thread.join()
