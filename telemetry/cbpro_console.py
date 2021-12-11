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

@click.group()
def cli():
    """A Coinbase API console using cbpro python library."""
    pass

@cli.command()
def get_products():
    """Get a list of available currency pairs for trading.

    \b
    Returns:
        list: Info about all currency pairs. Example::
            [
                {
                    "id": "BTC-USD",
                    "display_name": "BTC/USD",
                    "base_currency": "BTC",
                    "quote_currency": "USD",
                    "base_min_size": "0.01",
                    "base_max_size": "10000.00",
                    "quote_increment": "0.01"
                }
            ]

    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getproducts
    """

    public_client = cbpro.PublicClient()
    products = public_client.get_products()
    print(json.dumps(products, indent=4, sort_keys=True))

@cli.command()
@click.option('--product', prompt='Enter Product Id', help='Product Id (ie. BTC-USD)')
@click.option('--level', default=1, help='Order book level (1, 2, or 3)')
def get_product_order_book(product, level):
    """Get a list of open orders for a product.

    \b
    The amount of detail shown can be customized with the --level
    option:
    * 1: Only the best bid and ask
    * 2: Top 50 bids and asks (aggregated)
    * 3: Full order book (non aggregated)

    \b
    Level 1 and Level 2 are recommended for polling. For the most
    up-to-date data, consider using the websocket stream.

    \b
    **Caution**: Level 3 is only recommended for users wishing to
    maintain a full real-time order book using the websocket
    stream. Abuse of Level 3 via polling will cause your access to
    be limited or blocked.

    \b
    Returns:
        dict: Order book. Example for level 1::
            {
                "sequence": "3",
                "bids": [
                    [ price, size, num-orders ],
                ],
                "asks": [
                    [ price, size, num-orders ],
                ]
            }

    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getproductbook
    """

    public_client = cbpro.PublicClient()
    order_book = public_client.get_product_order_book(product, level=level)
    print(json.dumps(order_book, indent=4, sort_keys=True))

@cli.command()
@click.option('--product', prompt='Enter Product Id', help='Product Id (ie. BTC-USD)')
def get_product_ticker(product):
    """Snapshot of the last trade (tick), best bid/ask and 24h volume.

    **Caution**: Polling is discouraged in favor of connecting via
    the websocket stream and listening for match messages.

    \b
    Returns:
        dict: Ticker info. Example::
            {
              "trade_id": 4729088,
              "price": "333.99",
              "size": "0.193",
              "bid": "333.98",
              "ask": "333.99",
              "volume": "5957.11914015",
              "time": "2015-11-14T20:46:03.511254Z"
            }

    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getproductticker
    """

    public_client = cbpro.PublicClient()
    ticker = public_client.get_product_ticker(product)
    print(json.dumps(ticker, indent=4, sort_keys=True))

@cli.command()
@click.option('--product', prompt='Enter Product Id', help='Product Id (ie. BTC-USD)')
@click.option('--before', prompt='Before', help='Start time in ISO 8601')
@click.option('--after', prompt='After', help='End time in ISO 8601')
@click.option('--limit', default=100, help='The desired number of trades')
def get_product_trades(product, before, after, limit):
    """List the latest trade history for a product.

    This method returns a generator which may make multiple HTTP requests
    while iterating through it.

    **Caution**: Current released version of cbpro python library does not pass
    --before, --after, and --limit options to paginated request. These options
    thus have no effect.

    \b
    Returns:
        list: Latest trades. Example::
            [{
                "time": "2014-11-07T22:19:28.578544Z",
                "trade_id": 74,
                "price": "10.00000000",
                "size": "0.01000000",
                "side": "buy"
            }, {
                "time": "2014-11-07T01:08:43.642366Z",
                "trade_id": 73,
                "price": "100.00000000",
                "size": "0.01000000",
                "side": "sell"
            }]

    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getproducttrades
    """

    public_client = cbpro.PublicClient()

    # Returns a generator obj
    trades = public_client.get_product_trades(product_id=product,
                                            before=before,
                                            after=after,
                                            limit=limit)

    # Iterate through generator obj
    i = 0
    for x in trades:
        i += 1
        # Work-around for pagination bug until issue is resolved:
        # https://github.com/danpaquin/coinbasepro-python/pull/427
        if i > limit:
            break
        print(f"[{i}]:", json.dumps(x, indent=4, sort_keys=True))

@cli.command()
@click.option('--product', prompt='Enter Product Id', help='Product Id (ie. BTC-USD)')
@click.option('--start', help='(Optional) Start time in ISO 8601')
@click.option('--end', help='(Optional) End time in ISO 8601')
@click.option('--granularity', default=3600, help='Desired time slice in seconds')
def get_product_historic_rates(product, start, end, granularity):
    """List historic rates (candles) for a product.

    Rates are returned in grouped buckets based on requested
    granularity. If start, end, and granularity aren't provided,
    the exchange will assume some (currently unknown) default values.

    Historical rate data may be incomplete. No data is published for
    intervals where there are no ticks.

    **Caution**: Historical rates should not be polled frequently.
    If you need real-time information, use the trade and book
    endpoints along with the websocket feed.

    The maximum number of data points for a single request is 200
    candles. If your selection of start/end time and granularity
    will result in more than 200 data points, your request will be
    rejected. If you wish to retrieve fine granularity data over a
    larger time range, you will need to make multiple requests with
    new start/end ranges.

    \b
    Returns:
        list: Historic candle data. Example:
            [
                [ time, low, high, open, close, volume ],
                [ 1415398768, 0.32, 4.2, 0.35, 4.2, 12.3 ],
                ...
            ]

    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getproductcandles
    """

    public_client = cbpro.PublicClient()
    candles = public_client.get_product_historic_rates(product_id=product,
                                            start=start,
                                            end=end,
                                            granularity=granularity)
    print(json.dumps(candles, indent=4, sort_keys=True))

@cli.command()
@click.option('--product', prompt='Enter Product Id', help='Product Id (ie. BTC-USD)')
def get_product_24hr_stats(product):
    """Get 24 hr stats for the product.

    \b
    Returns:
        dict: 24 hour stats. Volume is in base currency units.
            Open, high, low are in quote currency units. Example::
            {
                "open": "34.19000000",
                "high": "95.70000000",
                "low": "7.06000000",
                "volume": "2.41000000"
            }

    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getproductstats
    """

    public_client = cbpro.PublicClient()
    stats = public_client.get_product_24hr_stats(product)
    print(json.dumps(stats, indent=4, sort_keys=True))

@cli.command()
def get_currencies():
    """List known currencies.

    \b
    Returns:
        list: List of currencies. Example::
            [{
                "id": "BTC",
                "name": "Bitcoin",
                "min_size": "0.00000001"
            }, {
                "id": "USD",
                "name": "United States Dollar",
                "min_size": "0.01000000"
            }]

    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getcurrencies
    """

    public_client = cbpro.PublicClient()
    currencies = public_client.get_currencies()
    print(json.dumps(currencies, indent=4, sort_keys=True))

@cli.command()
def get_time():
    """Get the API server time.

    \b
    Returns:
        dict: Server time in ISO and epoch format (decimal seconds
            since Unix epoch). Example::
                {
                    "iso": "2015-01-07T23:47:25.201Z",
                    "epoch": 1420674445.201
                }
    """

    public_client = cbpro.PublicClient()
    api_time = public_client.get_time()
    print(json.dumps(api_time, indent=4, sort_keys=True))

@cli.command()
@click.option('--product', prompt='Enter Product Id', help='Product Id (ie. BTC-USD)')
@click.option('--expiry', default=60, help='Time (in seconds) to remain subscribed')
def order_book(product, expiry):
    """Logs real-time changes to the bid-ask spread to console.

    The orderbook client will maintain a level3 order book and echo any changes
    to the terminal until the expiry time (default 60 seconds).
    """

    class OrderBookConsole(cbpro.OrderBook):
        def __init__(self, product_id=None):
            super(OrderBookConsole, self).__init__(product_id)

            # Latest values of bid-ask spread
            self._bid = None
            self._ask = None
            self._bid_depth = None
            self._ask_depth = None

        def on_message(self, message):
            super(OrderBookConsole, self).on_message(message)

            # Calculate newest bid-ask spread
            bid = self.get_bid()
            bids = self.get_bids(bid)
            bid_depth = sum([b['size'] for b in bids])
            ask = self.get_ask()
            asks = self.get_asks(ask)
            ask_depth = sum([a['size'] for a in asks])

            if self._bid == bid and self._ask == ask and self._bid_depth == bid_depth and self._ask_depth == ask_depth:
                # If there are no changes to the bid-ask spread since the last update, no need to print
                print("no change")
            else:
                # If there are differences, update the cache
                self._bid = bid
                self._ask = ask
                self._bid_depth = bid_depth
                self._ask_depth = ask_depth
                print('{} {} bid: {:.3f} @ {:.2f}\task: {:.3f} @ {:.2f}'.format(
                    dt.datetime.now(), self.product_id, bid_depth, bid, ask_depth, ask))

    order_book_console = OrderBookConsole(product)
    order_book_console.start()
    time.sleep(expiry)
    order_book_console.close()

@cli.command()
@click.option('--product', prompt='Enter Product Id', help='Product Id (ie. BTC-USD)')
@click.option('--channel', prompt='Enter Channel', help='Websocket channel to subscribe to')
@click.option('--expiry', default=10, help='Time (in seconds) to remain subscribed')
def subscribe(product, channel, expiry):
    """Subscribe to a websocket feed using the websocket client.

    The websocket client will remain subscribed and echo received messages to
    the terminal until the expiry time (default 10 seconds).

    \b
    Possible channels to subscribe:
    * "heartbeat"
    * "status"
    * "ticker"
    * "level2"
    * "full"
    * "user"
    * "matches"

    \b
    Detailed channel info can be found at:
    https://docs.cloud.coinbase.com/exchange/docs/channels
    """

    class MyWebsocketClient(cbpro.WebsocketClient):
        def on_open(self):
            self.message_count = 0

        def on_message(self, msg):
            print(json.dumps(msg, indent=4, sort_keys=True))
            self.message_count += 1

        def on_close(self):
            print("\n-- Socket Closed --")
            print("Total messages received: ", self.message_count)

    websocket_client = MyWebsocketClient(url="wss://ws-feed.pro.coinbase.com",
                                    products=[f"{product}"],
                                    channels=[f"{channel}"])
    websocket_client.start()
    time.sleep(expiry)
    websocket_client.close()

if __name__ == '__main__':
    cli()
