import time
import datetime as dt
import threading
import queue
import pandas
from decimal import Decimal
from sortedcontainers.sorteddict import SortedDict

from binance import Client
from binance.streams import ThreadedWebsocketManager
from base_level2_order_book import L2OrderBook
from auth_keys import (binance_api_secret, binance_api_key)

class Bi_L2OrderBook(L2OrderBook):
    def __init__(self, symbol='BNBBTC', tld='com', interval=100, log_to=None):
        self._symbol = symbol
        self._tld = tld
        self._interval = interval
        self._queue = queue.Queue()

        self._snapshot_id = 0
        self._asks = SortedDict()
        self._bids = SortedDict()
        self._update_time = None

        self._run_worker = False
        self._lock = threading.Lock()

        self._twm = ThreadedWebsocketManager(binance_api_key, binance_api_secret, tld=self._tld)
        self._twm.start()

    @property
    def product_id(self):
        """Order Book only supports a single product currently."""
        return self._symbol

    def on_message(self, message):
        self._queue.put(message)

    def worker(self):
        prev_final_id = 0
        while self._run_worker == True:
            msg = self._queue.get()
            event_type = msg['e']
            if event_type == 'depthUpdate':
                if msg['u'] <= self._snapshot_id:
                    # Drop any event where 'u' (final update Id in event) is less than
                    # the snapshot Id.
                    print(f"Dropping old event {msg['u']} <= {self._snapshot_id}")
                    self._queue.task_done()
                    continue

                if prev_final_id > 0 and msg['U'] != (prev_final_id+1):
                    # Each new event's 'U' (first update Id in event) should be equal to
                    # the previous event's 'u' + 1. If this is not the case, then we have
                    # an event gap and should resync the order book by taking a new snapshot.
                    print(f"Event gap detected! Expected: {prev_final_id+1} Actual: {msg['U']}")

                prev_final_id = msg['u']
                with self._lock:
                    self.apply_update(msg)

            elif event_type == 'exit':
                print(f"Binance {self.product_id} worker received exit message!")
            self._queue.task_done()

    def apply_snapshot(self, message):
        self._snapshot_id = message['lastUpdateId']
        #print("snapshot Id: ", self._snapshot_id)
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
        # Log the event time to keep track of possible de-sync.
        self._update_time = message['E']
        if self.product_id != message['s']:
            print(f"Unexpected Product Id. Received: {message['s']}, Expected: {self.product_id}")
            return

        for bids in message['b']:
            price = Decimal(bids[0])
            size = Decimal(bids[1])
            if size <= 0:
                self._bids.pop(price, default=0)
                #print("Removed bid price level: ", price)
            else:
                self._bids[price] = size
                #print(f"Bid price level {price} updated to size {size}")

        for asks in message['a']:
            price = Decimal(asks[0])
            size = Decimal(asks[1])
            if size <= 0:
                self._asks.pop(price, default=0)
                #print("Removed ask price level: ", price)
            else:
                self._asks[price] = size
                #print(f"Ask price level {price} updated to size {size}")

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
        # Start listening to the diff. depth stream. On message handler will queue received
        # messages for processing later.
        self._ds = self._twm.start_depth_socket(callback=self.on_message,
                                                symbol=self._symbol,
                                                interval=self._interval)

        # Short delay to let buffer fill up a bit. Otherwise, there will be an initial gap
        # between the snapshot update Id and the first diff update Id.
        time.sleep(1)

        # Get a depth snapshot from REST endpoint.
        # NOTE: Currently, Binance API is deficient when it comes to level 2 order book synchronization.
        # The initial snapshot truncates to a maximum depth of 5000 results, which does not capture
        # the full level 2 order book snapshot. Essentially, the local book is NEVER in sync with the
        # server book, although over time, the local book should get closer.
        # See: https://issueexplorer.com/issue/bmoscon/cryptofeed/604
        self._client = Client(binance_api_key, binance_api_secret, tld=self._tld)
        depth = self._client.get_order_book(symbol=self._symbol, limit=5000)
        self._client.close_connection()

        # Apply the initial snapshot to populate asks/bids.
        self.apply_snapshot(depth)

        # After the initial snapshot is done processing, turn on worker thread to begin
        # replaying buffered messages.
        self._run_worker = True
        self._worker_thread = threading.Thread(target=self.worker, daemon=True)
        self._worker_thread.start()

    def destroy(self):
        # Bring down the producer first by calling stop socket on depth socket.
        self._twm.stop_socket(self._ds)
        # Wait for any lingering messages to be processed. Ensures queue is drained before continuing.
        self._queue.join()
        # Mark the worker thread to stop running.
        self._run_worker = False
        # Since we've ensured the queue is empty from the previous join(), the worker thread is currently
        # blocking indefinitely on an empty queue. Here we'll use the poison pill technique to send one
        # final "special" message to cause the worker thread to loop one final time, then exit.
        self._queue.put({"e":"exit"})
        self._worker_thread.join()
        
        # Clearing the queue not required because of update time check.
        #self._queue.clear()

    def get_update_time(self):
        return self._update_time

    def export(self):
        with self._lock:
            return self.export_grouped_snapshot()

    def check_uptime(self, time_now):
        # Convert the stored update time to datetime format for comparison.
        dt_update_time = dt.datetime.utcfromtimestamp(int(self._update_time)//1000)
        dt_delta = time_now - dt_update_time
        # If the last event update time is stale by more than 10 seconds, attempt restarting order book.
        if dt_delta.total_seconds() > 10:
            print(f"WARNING: Binance {self._symbol} last updated: {dt_update_time} vs current time: {time_now} (delta: {dt_delta}). Attempting reset.")
            self.destroy()
            self.create()

if __name__ == '__main__':
    bn_order_book = Bi_L2OrderBook(symbol="SOLUSDT")
    bn_order_book.create()

    while True:
        bn_order_book_depth = bn_order_book.export()
        print(bn_order_book_depth)
        time.sleep(1)
