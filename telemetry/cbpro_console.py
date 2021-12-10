import sys
import getopt
import logging
import os
import socket
import threading
import time
import json
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
