import time
import json
from binance.streams import ThreadedWebsocketManager
import click
import asyncio
from sortedcontainers.sorteddict import SortedDict
from auth_keys import (binance_api_secret, binance_api_key)
from binance import AsyncClient, ThreadedDepthCacheManager

async def main():
    
    symbol = 'SOLUSDT'

    twm = ThreadedWebsocketManager(binance_api_key, binance_api_secret)
    twm.start()

    def on_socket_message(msg):
        print(f"message type: {msg['e']}")
        print(msg)

    twm.start_depth_socket(callback=on_socket_message, symbol=symbol, interval=100)

    twm.join()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())