import time
import json
import click
import asyncio
import threading
import queue
from sortedcontainers.sorteddict import SortedDict
from auth_keys import (binance_api_secret, binance_api_key)
from binance import AsyncClient, ThreadedDepthCacheManager
from binance.streams import ThreadedWebsocketManager
from base_level2_order_book import L2OrderBook

class Bn_L2OrderBook(L2OrderBook):
    def __init__(self, symbol='BNBBTC', interval=100, log_to=None):
        self._symbol = symbol
        self._interval = interval
        self._queue = queue.Queue()

        self._asks = SortedDict()
        self._bids = SortedDict()
        self._update_time = None

    @property
    def product_id(self):
        """Order Book only supports a single product currently."""
        return self._symbol

    def on_message(self, msg):
        self._queue.put(msg)
        #print("msg: ", msg)
        print("Enqueue - size: ", self._queue.qsize())

    def worker(self):
        while True:
            msg = self._queue.get()
            print("Dequeue - size: ", self._queue.qsize())

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
        time.sleep(3)

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
    bn_order_book = Bn_L2OrderBook(symbol="SOLUSDT")
    bn_order_book.create()
