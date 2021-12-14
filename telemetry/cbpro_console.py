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
import matplotlib.pyplot as plt

from cbpro_level2_order_book import L2OrderBook

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
@click.option('--sandbox/--no-sandbox', default=True, help='Target sandbox or live API (default is sandbox)')
def auth_get_accounts(sandbox):
    """ Get a list of all trading accounts.

    When you place an order, the funds for the order are placed on
    hold. They cannot be used for other orders or withdrawn. Funds
    will remain on hold until the order is filled or canceled. The
    funds on hold for each account will be specified.

    \b
    Returns:
        list: Info about all accounts. Example::
            [
                {
                    "id": "71452118-efc7-4cc4-8780-a5e22d4baa53",
                    "currency": "BTC",
                    "balance": "0.0000000000000000",
                    "available": "0.0000000000000000",
                    "hold": "0.0000000000000000",
                    "profile_id": "75da88c5-05bf-4f54-bc85-5c775bd68254"
                },
                {
                    ...
                }
            ]
    * Additional info included in response for margin accounts.

    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getaccounts
    """
    if sandbox:
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass,
                                            api_url="https://api-public.sandbox.pro.coinbase.com")
    else:
        print("WARNING: Connecting to Live Coinbase API!")
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)
 
    accounts = auth_client.get_accounts()
    print(json.dumps(accounts, indent=4, sort_keys=True))

@cli.command()
@click.option('--sandbox/--no-sandbox', default=True, help='Target sandbox or live API (default is sandbox)')
@click.option('--account_id', prompt='Enter Account Id', help='Account Id to get history of')
def auth_get_account_history(sandbox, account_id):
    """ List account activity (ledger). Account activity either increases or
    decreases your account balance.

    \b
    Entry type indicates the reason for the account change.
    * transfer:	Funds moved to/from Coinbase to cbpro
    * match:	Funds moved as a result of a trade
    * fee:	    Fee as a result of a trade
    * rebate:   Fee rebate as per our fee schedule

    \b
    If an entry is the result of a trade (match, fee), the details
    field will contain additional information about the trade.

    \b
    Returns:
        list: History information for the account. Example::
            [
                {
                    "id": "100",
                    "created_at": "2014-11-07T08:19:27.028459Z",
                    "amount": "0.001",
                    "balance": "239.669",
                    "type": "fee",
                    "details": {
                        "order_id": "d50ec984-77a8-460a-b958-66f114b0de9b",
                        "trade_id": "74",
                        "product_id": "BTC-USD"
                    }
                },
                {
                    ...
                }
            ]

    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getaccountledger
    """

    if sandbox:
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass,
                                            api_url="https://api-public.sandbox.pro.coinbase.com")
    else:
        print("WARNING: Connecting to Live Coinbase API!")
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)

    # Returns a generator obj
    g_account_history = auth_client.get_account_history(account_id)

    # Iterate through generator obj
    for entry in g_account_history:
        print(json.dumps(entry, indent=4, sort_keys=True))

@cli.command()
@click.option('--sandbox/--no-sandbox', default=True, help='Target sandbox or live API (default is sandbox)')
@click.option('--account_id', prompt='Enter Account Id', help='Account Id to get history of')
def auth_get_account_holds(sandbox, account_id):
    """ Get holds on an account.
    
    This method returns a generator which may make multiple HTTP requests
    while iterating through it.

    Holds are placed on an account for active orders or
    pending withdraw requests.

    As an order is filled, the hold amount is updated. If an order
    is canceled, any remaining hold is removed. For a withdraw, once
    it is completed, the hold is removed.

    The "type" field will indicate why the hold exists. The hold
    type is "order" for holds related to open orders and 'transfer'
    for holds related to a withdraw.

    The "ref" field contains the id of the order or transfer which
    created the hold.
    
    \b
    Returns:
        generator(list): Hold information for the account. Example::
            [
                {
                    "id": "82dcd140-c3c7-4507-8de4-2c529cd1a28f",
                    "account_id": "e0b3f39a-183d-453e-b754-0c13e5bab0b3",
                    "created_at": "2014-11-06T10:34:47.123456Z",
                    "updated_at": "2014-11-06T10:40:47.123456Z",
                    "amount": "4.23",
                    "type": "order",
                    "ref": "0a205de4-dd35-4370-a285-fe8fc375a273",
                },
                {
                ...
                }
            ]
    
    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getaccountholds
    """

    if sandbox:
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass,
                                            api_url="https://api-public.sandbox.pro.coinbase.com")
    else:
        print("WARNING: Connecting to Live Coinbase API!")
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)

    # Returns a generator obj
    g_account_holds = auth_client.get_account_holds(account_id)

    # Iterate through generator obj
    for entry in g_account_holds:
        print(json.dumps(entry, indent=4, sort_keys=True))

@cli.command()
@click.option('--sandbox/--no-sandbox', default=True, help='Target sandbox or live API (default is sandbox)')
@click.option('--product', prompt='Enter Product Id', help='Product Id (ie. BTC-USD)')
@click.option('--side', prompt='Enter buy or sell', help='Order side (buy or sell)')
@click.option('--price', prompt='Enter price', help='Price per cryptocurrency')
@click.option('--size', prompt='Enter size', help='Amount of cryptocurrency to buy or sell')
def auth_place_limit_order(sandbox, product, side, price, size):
    """Place a limit order.
    
    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_postorders
    """
    
    if sandbox:
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass,
                                            api_url="https://api-public.sandbox.pro.coinbase.com")
    else:
        print("WARNING: Connecting to Live Coinbase API!")
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)

    # Limit order specific method
    ret = auth_client.place_limit_order(product_id=product,
                                        side=side,
                                        price=price,
                                        size=size)
    # Print result code
    print(json.dumps(ret, indent=4, sort_keys=True))

@cli.command()
@click.option('--sandbox/--no-sandbox', default=True, help='Target sandbox or live API (default is sandbox)')
@click.option('--product', prompt='Enter Product Id', help='Product Id (ie. BTC-USD)')
@click.option('--side', prompt='Enter buy or sell', help='Order side (buy or sell)')
@click.option('--funds', default=None, help='(Optional) Desired amount of quote currency to use. Specify this or "size"')
@click.option('--size', default=None, help='(Optional) Desired amount of cryptocurrency. Specify this or "funds"')
def auth_place_market_order(sandbox, product, side, funds, size):
    """Place a market order.
    
    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_postorders
    """

    if funds is None and size is None:
        print("Must provide either --funds or --size options")
        return
    
    if sandbox:
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass,
                                            api_url="https://api-public.sandbox.pro.coinbase.com")
    else:
        print("WARNING: Connecting to Live Coinbase API!")
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)

    # Market order specific method
    ret = auth_client.place_market_order(product_id=product,
                                        side=side,
                                        funds=funds,
                                        size=size)
    # Print result code
    print(json.dumps(ret, indent=4, sort_keys=True))

@cli.command()
@click.option('--sandbox/--no-sandbox', default=True, help='Target sandbox or live API (default is sandbox)')
@click.option('--order_id', prompt='Enter Order Id', help='The order_id of the order to cancel')
def auth_cancel_order(sandbox, order_id):
    """ Cancel a previously placed order.

    If the order had no matches during its lifetime its record may
    be purged. This means the order details will not be available
    with get_order(order_id). If the order could not be canceled
    (already filled or previously canceled, etc), then an error
    response will indicate the reason in the message field.

    **Caution**: The order id is the server-assigned order id and
    not the optional client_oid.

    \b
    Returns:
        list: Containing the order_id of cancelled order. Example::
            [ "c5ab5eae-76be-480e-8961-00792dc7e138" ]

    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_deleteorder
    """

    if sandbox:
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass,
                                            api_url="https://api-public.sandbox.pro.coinbase.com")
    else:
        print("WARNING: Connecting to Live Coinbase API!")
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)

    ret = auth_client.cancel_order(order_id)
    print(json.dumps(ret, indent=4, sort_keys=True))

@cli.command()
@click.option('--sandbox/--no-sandbox', default=True, help='Target sandbox or live API (default is sandbox)')
@click.option('--product', default=None, help='(Optional) Only cancel orders for this product')
def auth_cancel_all(sandbox, product):
    """Attempt to cancel all orders
    
    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_deleteorders
    """

    if sandbox:
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass,
                                            api_url="https://api-public.sandbox.pro.coinbase.com")
    else:
        print("WARNING: Connecting to Live Coinbase API!")
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)

    ret = auth_client.cancel_all(product_id=product)
    print(json.dumps(ret, indent=4, sort_keys=True))

@cli.command()
@click.option('--sandbox/--no-sandbox', default=True, help='Target sandbox or live API (default is sandbox)')
def auth_get_orders(sandbox):
    """ List your current open orders.

    This method returns a generator which may make multiple HTTP requests
    while iterating through it.

    Only open or un-settled orders are returned. As soon as an
    order is no longer open and settled, it will no longer appear
    in the default request.

    Orders which are no longer resting on the order book, will be
    marked with the 'done' status. There is a small window between
    an order being 'done' and 'settled'. An order is 'settled' when
    all of the fills have settled and the remaining holds (if any)
    have been removed.

    For high-volume trading it is strongly recommended that you
    maintain your own list of open orders and use one of the
    streaming market data feeds to keep it updated. You should poll
    the open orders endpoint once when you start trading to obtain
    the current state of any open orders.
    
    \b
    Returns:
        list: Containing information on orders. Example::
            [
                {
                    "id": "d0c5340b-6d6c-49d9-b567-48c4bfca13d2",
                    "price": "0.10000000",
                    "size": "0.01000000",
                    "product_id": "BTC-USD",
                    "side": "buy",
                    "stp": "dc",
                    "type": "limit",
                    "time_in_force": "GTC",
                    "post_only": false,
                    "created_at": "2016-12-08T20:02:28.53864Z",
                    "fill_fees": "0.0000000000000000",
                    "filled_size": "0.00000000",
                    "executed_value": "0.0000000000000000",
                    "status": "open",
                    "settled": false
                },
                {
                    ...
                }
            ]

    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getorders
    """

    if sandbox:
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass,
                                            api_url="https://api-public.sandbox.pro.coinbase.com")
    else:
        print("WARNING: Connecting to Live Coinbase API!")
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)

    # Returns a generator obj
    g_orders = auth_client.get_orders()

    # Iterate through generator obj
    for entry in g_orders:
        print(json.dumps(entry, indent=4, sort_keys=True))

@cli.command()
@click.option('--sandbox/--no-sandbox', default=True, help='Target sandbox or live API (default is sandbox)')
@click.option('--product', default=None, help='Limit list to this product id')
@click.option('--order_id', default=None, help='Limit list to this order id')
def auth_get_fills(sandbox, product, order_id):
    """ Get a list of recent fills.

    As of 8/23/18 - Requests without either order_id or product_id
    will be rejected.

    This method returns a generator which may make multiple HTTP requests
    while iterating through it.

    Fees are recorded in two stages. Immediately after the matching
    engine completes a match, the fill is inserted into our
    datastore. Once the fill is recorded, a settlement process will
    settle the fill and credit both trading counterparties.

    The 'fee' field indicates the fees charged for this fill.

    The 'liquidity' field indicates if the fill was the result of a
    liquidity provider or liquidity taker. M indicates Maker and T
    indicates Taker.

    \b
    Returns:
        list: Containing information on fills. Example::
            [
                {
                    "trade_id": 74,
                    "product_id": "BTC-USD",
                    "price": "10.00",
                    "size": "0.01",
                    "order_id": "d50ec984-77a8-460a-b958-66f114b0de9b",
                    "created_at": "2014-11-07T22:19:28.578544Z",
                    "liquidity": "T",
                    "fee": "0.00025",
                    "settled": true,
                    "side": "buy"
                },
                {
                    ...
                }
            ]

    \b
    Coinbase API Documentation:
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getfills
    """

    if product is None and order_id is None:
        print("Must provide either --product or --order_id options")
        return

    if sandbox:
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass,
                                            api_url="https://api-public.sandbox.pro.coinbase.com")
    else:
        print("WARNING: Connecting to Live Coinbase API!")
        auth_client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)

    # Returns a generator obj
    g_fills = auth_client.get_fills(product_id=product, order_id=order_id)

    # Iterate through generator obj
    for entry in g_fills:
        print(json.dumps(entry, indent=4, sort_keys=True))

@cli.command()
@click.option('--product', prompt='Enter Product Id', help='Product Id (ie. BTC-USD)')
@click.option('--expiry', default=60, help='Time (in seconds) to remain subscribed')
def level3_order_book(product, expiry):
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
    print(order_book_console.get_current_book())
    order_book_console.close()

@cli.command()
@click.option('--product', prompt='Enter Product Id', help='Product Id (ie. BTC-USD)')
@click.option('--expiry', default=60, help='Time (in seconds) to remain subscribed')
def level2_order_book(product, expiry):
    """Maintain a real-time level 2 order book."""

    # Start the L2 order book and keep subscribed until expiry.
    l2_order_book = L2OrderBook(product_id=product)
    l2_order_book.start()
    time.sleep(expiry)
    l2_order_book.close()

    # Export the final snapshot of the aggregated order book.
    book = l2_order_book.export_grouped_snapshot()
    print(book[0])
    print(book[1])
    
    # Convert order book to json
    asks_json = book[0].to_json()
    bids_json = book[1].to_json()
    print(asks_json)
    print(bids_json)

    # Verify it can be converted back
    asks_dict = json.loads(asks_json)
    bids_dict = json.loads(bids_json)
    asks_df = pandas.DataFrame.from_dict(asks_dict)
    bids_df = pandas.DataFrame.from_dict(bids_dict)
    print(asks_df)
    print(bids_df)

    # Plot bar chart of grouped asks and bids.
    book[1]['size'] = book[1]['size'].apply(pandas.to_numeric)
    book[1].plot.bar(y='size') # x defaults to index
    book[0]['size'] = book[0]['size'].apply(pandas.to_numeric)
    book[0].plot.bar(y='size') # x defaults to index
    plt.show()

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
                                    #products=['SOL-USD', 'SOL-EUR', 'SOL-BTC'],
                                    channels=[f"{channel}"])
    websocket_client.start()
    time.sleep(expiry)
    websocket_client.close()

if __name__ == '__main__':
    cli()
