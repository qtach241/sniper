import sys
import time
import json
import cbpro

from auth_keys import (api_secret, api_key, api_pass)

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
