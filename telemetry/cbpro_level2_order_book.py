import json
import time
import datetime as dt
import cbpro
from decimal import Decimal
from sortedcontainers.sorteddict import SortedDict

import pprint

class L2OrderBook(cbpro.WebsocketClient):
    def __init__(self, product_id='BTC-USD', log_to=None):
        super(L2OrderBook, self).__init__(products=product_id, channels=['level2'])
        self._asks = SortedDict()
        self._bids = SortedDict()
        
    def apply_snapshot(self, message):
        self._asks.clear()
        self._bids.clear()
        for bid in message['bids']:
            price = Decimal(bid[0])
            size = Decimal(bid[1])
            self._bids[price] = size
        for ask in message['asks']:
            price = Decimal(ask[0])
            size = Decimal(ask[1])
            self._asks[price] = size

    def apply_update(self, message):
        for change in message['changes']:
            side = change[0]
            price = Decimal(change[1])
            size = Decimal(change[2]) 
            if side == 'buy':
                if size <= 0:
                    self._bids.pop(price)
                    #print("Removed bid price level: ", price)
                else:
                    self._bids[price] = size
                    #print(f"Bid price level {price} updated to size {size}")
            elif side == 'sell':
                if size <= 0:
                    self._asks.pop(price)
                    #print("Removed ask price level: ", price)
                else:
                    self._asks[price] = size
                    #print(f"Ask price level {price} updated to size {size}")

    def on_message(self, message):
        msg_type = message['type']
        if msg_type == 'subscription':
            pass
        elif msg_type == 'snapshot':
            self.apply_snapshot(message)
            #pprint.pprint(self._asks.items())
            #pprint.pprint(self._bids.items())
        elif msg_type == 'l2update':
            self.apply_update(message)
            print(f"bid: {self.get_bid()}, ask: {self.get_ask()}, spread: {self.get_spread()}, price: {self.get_mid_market_price()}")

    def get_ask(self):
        return self._asks.peekitem(0)[0]

    def get_bid(self):
        return self._bids.peekitem(-1)[0]

    def get_spread(self):
        return (self.get_ask() - self.get_bid())

    def get_mid_market_price(self):
        return (self.get_bid() + (self.get_spread()/2))