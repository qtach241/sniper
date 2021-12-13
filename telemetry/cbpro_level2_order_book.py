import json
import time
import datetime as dt
import cbpro
from decimal import Decimal
from sortedcontainers.sorteddict import SortedDict
import pandas

import pprint

class L2OrderBook(cbpro.WebsocketClient):
    def __init__(self, product_id='BTC-USD', log_to=None):
        super(L2OrderBook, self).__init__(products=product_id, channels=['level2'])
        self._asks = SortedDict()
        self._bids = SortedDict()

    @property
    def product_id(self):
        """Order Book only supports a single product currently."""
        return self.products[0]
        
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
        # TODO: Compare current time with "time" key and if too much slippage,
        # re-subscribe to the feed and sync to the new snapshot.
        # msg_time = message['time']
        if self.product_id != message['product_id']:
            print(f"Unexpected Product Id. Received: {message['product_id']}, Expected: {self.product_id}")
            return

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
            #print(f"bid: {self.get_bid()}, ask: {self.get_ask()}, spread: {self.get_spread()}, price: {self.get_mid_market_price()}")

    def get_ask(self):
        return self._asks.peekitem(0)[0]

    def get_bid(self):
        return self._bids.peekitem(-1)[0]

    def get_spread(self):
        return self.get_ask() - self.get_bid()

    def get_mid_market_price(self):
        return (self.get_bid() + (self.get_spread()/2))

    def export_raw_snapshot(self):
        df_asks = pandas.DataFrame(list(self._asks.items()), columns=['price', 'size'])
        df_bids = pandas.DataFrame(list(self._bids.items()), columns=['price', 'size'])
        return (df_asks, df_bids)

    def export_grouped_snapshot(self):
        # First get the raw ask and bid dataframes.
        raw = self.export_raw_snapshot()

        # We will group the raw dataframe into 10 bins. The bin edges must be calculated
        # dynamically based on the ask and bid.
        ask = self.get_ask()
        ask_labels = ['ASK_0009', 'ASK_0019', 'ASK_0039', 'ASK_0078', 'ASK_0156', 'ASK_0313', 'ASK_0625', 'ASK_1250', 'ASK_2500', 'ASK_5000']
        ask_bins = [ask, ask+(ask/1024), ask+(ask/512), ask+(ask/256), ask+(ask/128), ask+(ask/64), ask+(ask/32), ask+(ask/16), ask+(ask/8), ask+(ask/4), ask+(ask/2)]
        
        bid = self.get_bid()
        bid_labels = ['BID_5000', 'BID_2500', 'BID_1250', 'BID_0625', 'BID_0313', 'BID_0156', 'BID_0078', 'BID_0039', 'BID_0019', 'BID_0009']
        bid_bins = [bid-(bid/2), bid-(bid/4), bid-(bid/8), bid-(bid/16), bid-(bid/32), bid-(bid/64), bid-(bid/128), bid-(bid/256), bid-(bid/512), bid-(bid/1024), bid]
        
        # Now add new column 'price_bins' to the dataframe and sort data into bins.
        raw[0]['price_bins'] = pandas.cut(raw[0]['price'], bins=ask_bins, labels=ask_labels, include_lowest=True)
        raw[1]['price_bins'] = pandas.cut(raw[1]['price'], bins=bid_bins, labels=bid_labels, include_lowest=True)

        # Aggregate price and size into the 10 bins (dropping any that were out of range)
        grouped_asks = raw[0].groupby('price_bins', as_index=False).agg({'price': ['min', 'max'], 'size': 'sum'})
        grouped_bids = raw[1].groupby('price_bins', as_index=False).agg({'price': ['min', 'max'], 'size': 'sum'})

        return (grouped_asks, grouped_bids)
