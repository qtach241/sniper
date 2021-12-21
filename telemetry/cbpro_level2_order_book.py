import json
import time
import queue
import threading
import datetime as dt
import cbpro
from decimal import Decimal
from sortedcontainers.sorteddict import SortedDict
import pandas

from base_level2_order_book import L2OrderBook

class Cb_L2OrderBook(cbpro.WebsocketClient, L2OrderBook):
    def __init__(self, product_id='BTC-USD', log_to=None):
        super(Cb_L2OrderBook, self).__init__(products=product_id, channels=['level2'])
        self._asks = SortedDict()
        self._bids = SortedDict()
        self._update_time = None
        self._queue = queue.Queue()

        self._run_worker = False
        self._lock = threading.Lock()

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
        # Log the event time to keep track of possible de-sync in check_uptime().
        self._update_time = message['time']
        if self.product_id != message['product_id']:
            print(f"Unexpected Product Id. Received: {message['product_id']}, Expected: {self.product_id}")
            return

        for change in message['changes']:
            side = change[0]
            price = Decimal(change[1])
            size = Decimal(change[2])
            if side == 'buy':
                if size <= 0:
                    self._bids.pop(price, default=0)
                    #print("Removed bid price level: ", price)
                else:
                    self._bids[price] = size
                    #print(f"Bid price level {price} updated to size {size}")
            elif side == 'sell':
                if size <= 0:
                    self._asks.pop(price, default=0)
                    #print("Removed ask price level: ", price)
                else:
                    self._asks[price] = size
                    #print(f"Ask price level {price} updated to size {size}")

    def on_message(self, message):
        self._queue.put(message)

    def worker(self):
        # Coinbase's websocket API actually guarantees sequential delivery of messages
        # on the level2 channel. Thus, no need to check sequence id, or event times here.
        while self._run_worker == True:
            message = self._queue.get()
            msg_type = message['type']
            if msg_type == 'subscription':
                pass
            elif msg_type == 'snapshot':
                with self._lock:
                    self.apply_snapshot(message)
                    #pprint.pprint(self._asks.items())
                    #pprint.pprint(self._bids.items())
            elif msg_type == 'l2update':
                with self._lock:
                    self.apply_update(message)
                    #print(f"bid: {self.get_bid()}, ask: {self.get_ask()}, spread: {self.get_spread()}, price: {self.get_mid_market_price()}")
            elif msg_type == 'exit':
                print(f"Cbpro {self.product_id} worker received exit message!")
            self._queue.task_done()

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
        bid = self.get_bid()
        ask_bins = self.get_ask_bins(ask)
        bid_bins = self.get_bid_bins(bid)
        
        # Now add new column 'price_bins' to the dataframe and sort data into bins.
        raw[0]['price_bins'] = pandas.cut(raw[0]['price'], bins=ask_bins, labels=self.ASK_LABELS, include_lowest=True)
        raw[1]['price_bins'] = pandas.cut(raw[1]['price'], bins=bid_bins, labels=self.BID_LABELS, include_lowest=True)

        # Aggregate price and size into the 10 bins (dropping any that were out of range)
        #grouped_asks = raw[0].groupby('price_bins', as_index=True).agg({'price': ['min', 'max'], 'size': 'sum'})
        #grouped_bids = raw[1].groupby('price_bins', as_index=True).agg({'price': ['min', 'max'], 'size': 'sum'})
        grouped_asks = raw[0].groupby('price_bins', as_index=True).agg({'size': 'sum'})
        grouped_bids = raw[1].groupby('price_bins', as_index=True).agg({'size': 'sum'})

        return (grouped_asks, grouped_bids, ask, bid)

    # Implement base_level2_order_book interface:
    def create(self):
        super(Cb_L2OrderBook, self).start()
        self._run_worker = True
        self._worker_thread = threading.Thread(target=self.worker, daemon=True)
        self._worker_thread.start()

    def destroy(self):
        # Bring down the producer first.
        super(Cb_L2OrderBook, self).close()
        # Wait for any lingering messages to be processed. Ensures queue is drained before continuing.
        self._queue.join()
        # Mark the worker thread to stop running.
        self._run_worker = False
        # Since we've ensured the queue is empty from the previous join(), the worker thread is currently
        # blocking indefinitely on an empty queue. Here we'll use the poison pill technique to send one
        # final "special" message to cause the worker thread to loop one final time, then exit.
        self._queue.put({"type":"exit"})
        self._worker_thread.join()

    def get_update_time(self):
        return self._update_time

    def export(self):
        with self._lock:
            return self.export_grouped_snapshot()

    def check_uptime(self, time_now):
        # Convert the stored update time to datetime format for comparison.
        # For Cbpro order books, update time is stored as an ISO string with trailing Z notation
        # which python doesn't like for some reason so remove it.
        dt_update_time_iso = self._update_time[:-1]
        dt_update_time = dt.datetime.fromisoformat(dt_update_time_iso)
        dt_delta = time_now - dt_update_time
        # If the last event update time is stale by more than 10 seconds, attempt restarting order book.
        if dt_delta.total_seconds() > 10:
            print(f"WARNING: Cbpro {self.product_id} last updated: {dt_update_time} vs current time: {time_now} (delta: {dt_delta}). Attempting reset.")
            self.destroy()
            self.create()
