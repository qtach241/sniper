import time
import json
import click
import asyncio
import threading
import queue
from decimal import Decimal
from sortedcontainers.sorteddict import SortedDict
from auth_keys import (binance_api_secret, binance_api_key)
from binance import Client, AsyncClient, ThreadedDepthCacheManager
from binance.streams import ThreadedWebsocketManager
from base_level2_order_book import L2OrderBook

class Bn_L2OrderBook(L2OrderBook):
    def __init__(self, symbol='BNBBTC', interval=100, log_to=None):
        self._symbol = symbol
        self._interval = interval
        self._queue = queue.Queue()

        self._snapshot_id = 0
        self._asks = SortedDict()
        self._bids = SortedDict()
        self._update_time = None

    @property
    def product_id(self):
        """Order Book only supports a single product currently."""
        return self._symbol

    def on_message(self, message):
        event_type = message['e']
        if event_type == 'depthUpdate':
            self._queue.put(message)
            #print("msg: ", message)
            print("Enqueue - size: ", self._queue.qsize())
        else:
            print("on_message unrecognized event type: ", event_type)

    def worker(self):
        prev_final_id = 0
        while True:
            msg = self._queue.get()
            print("Dequeue - size: ", self._queue.qsize())
            if msg['u'] <= self._snapshot_id:
                # Drop any event where 'u' (final update Id in event) is less than
                # the snapshot Id.
                print(f"Dropping old event {msg['u']} less than {self._snapshot_id}")
                continue

            if prev_final_id > 0 and msg['U'] != (prev_final_id+1):
                # Each new event's 'U' (first update Id in event) should be equal to
                # the previous event's 'u' + 1. If this is not the case, then we have
                # an event gap and should resync the order book by taking a new snapshot.
                print(f"Event gap detected! Expected: {prev_final_id+1} Actual: {msg['U']}")

            prev_final_id = msg['u']
            self.apply_update(msg)

    def apply_snapshot(self, message):
        self._snapshot_id = message['lastUpdateId']
        print("snapshot Id: ", self._snapshot_id)
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
                print("Removed bid price level: ", price)
            else:
                self._bids[price] = size
                print(f"Bid price level {price} updated to size {size}")

        for asks in message['a']:
            price = Decimal(asks[0])
            size = Decimal(asks[1])
            if size <= 0:
                self._asks.pop(price, default=0)
                print("Removed ask price level: ", price)
            else:
                self._asks[price] = size
                print(f"Ask price level {price} updated to size {size}")

    # Implement base_level2_order_book interface:
    def create(self):
        self._twm = ThreadedWebsocketManager(binance_api_key, binance_api_secret)
        self._twm.start()

        # Start listening to the diff. depth stream. On message handler will queue received
        # messages for processing later.
        self._ds = self._twm.start_depth_socket(callback=self.on_message,
                                                symbol=self._symbol,
                                                interval=self._interval)

        # Get a depth snapshot from REST endpoint
        self._client = Client(binance_api_key, binance_api_secret)
        depth = self._client.get_order_book(symbol=self._symbol, limit=5000)
        self.apply_snapshot(depth)

        # After the initial snapshot is done processing, turn on worker thread to begin
        # replaying buffered messages.
        threading.Thread(target=self.worker, daemon=True).start()

    def destroy(self):
        self._twm.stop_socket(self._ds)

    def get_update_time(self):
        return self._update_time

    def export(self):
        #return self.export_grouped_snapshot()
        pass

if __name__ == '__main__':
    bn_order_book = Bn_L2OrderBook(symbol="BTCUSDT")
    bn_order_book.create()
