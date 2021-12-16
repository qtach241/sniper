import time
import json
import click
from sortedcontainers.sorteddict import SortedDict
from auth_keys import (binance_api_secret, binance_api_key)
from binance import Client, ThreadedDepthCacheManager

@click.group()
@click.option('--tld', default='com', help='Top level domain (default: com)')
@click.pass_context
def cli(ctx, tld):
    """A Binance API console using binance-python library."""
    ctx.ensure_object(dict)
    ctx.obj['client'] = Client(binance_api_key, binance_api_secret, tld=tld)

@cli.command()
@click.pass_context
def get_exchange_info(ctx):
    """Get info about the exchange."""
    
    info = ctx.obj['client'].get_exchange_info()
    print(json.dumps(info, indent=4, sort_keys=True))

@cli.command()
@click.pass_context
@click.option('--symbol', prompt='Enter Symbol', help='Binance symbol (ie. BNBBTC)')
def get_symbol_info(ctx, symbol):
    """Get info about a particular symbol."""

    info = ctx.obj['client'].get_symbol_info(symbol)
    print(json.dumps(info, indent=4, sort_keys=True))

@cli.command()
@click.pass_context
def get_all_tickers(ctx):
    """Get all symbol prices."""

    prices = ctx.obj['client'].get_all_tickers()
    print(json.dumps(prices, indent=4, sort_keys=True))

@cli.command()
@click.pass_context
@click.option('--symbol', prompt='Enter Symbol', help='Binance symbol (ie. BNBBTC)')
def get_order_book(ctx, symbol):
    """Get market depth."""

    depth = ctx.obj['client'].get_order_book(symbol=symbol)
    print(json.dumps(depth, indent=4, sort_keys=True))

@cli.command()
@click.pass_context
@click.option('--symbol', prompt='Enter Symbol', help='Binance symbol (ie. BNBBTC)')
def depth_cache_manager(ctx, symbol):
    """Start a depth cache manager for a symbol."""

    def handle_dcm_message(depth_cache):
        #print(f"symbol {depth_cache.symbol}")
        #print("top 5 bids")
        #print(depth_cache.get_bids()[:5])
        #print("top 5 asks")
        #print(depth_cache.get_asks()[:5])
        print("last update time {}".format(depth_cache.update_time))
        asks = depth_cache.get_asks()
        bids = depth_cache.get_bids()
        print(asks)
        print(bids)

    dcm = ThreadedDepthCacheManager()
    # start is required to initialise its internal loop
    dcm.start()
    time.sleep(2)

    dcm_name = dcm.start_depth_cache(callback=handle_dcm_message, symbol=symbol)
    # multiple depth caches can be started
    #dcm_name = dcm.start_depth_cache(callback=handle_dcm_message, symbol='BNBBTC')
    #dcm_name = dcm.start_depth_cache(callback=handle_dcm_message, symbol='ETHBTC')

    dcm.join()

if __name__ == '__main__':
    cli(obj={})
