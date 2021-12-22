import pandas as pd
import requests
import json
import datetime as dt
import time

def fetch_data(symbol, start, end):
    pair_split = symbol.split('/') # Symbol must be in format XXX/XXX ie. BTC/USD.
    symbol = pair_split[0] + '-' + pair_split[1]
    url = f'https://api.pro.coinbase.com/products/{symbol}/candles?granularity=60&start={start}&end={end}'
    response = requests.get(url)
    if response.status_code == 200:  # Check to make sure the response from server is good.
        data = pd.DataFrame(json.loads(response.text), columns=['unix', 'low', 'high', 'open', 'close', 'volume'])
        data['date'] = pd.to_datetime(data['unix'], unit='s')  # Convert to a readable date.
        data['vol_fiat'] = data['volume'] * data['close']      # Multiply the coin volume by closing price to approximate fiat volume.

        # If we failed to get any data, print an error...otherwise write the file.
        if data is None:
            print("Did not return any data from Coinbase for this symbol")
        else:
            data.to_csv(f'Coinbase_{pair_split[0] + pair_split[1]}_data.csv', mode='a', index=False, header=False)

    else:
        print("Did not receieve OK response from Coinbase API")


if __name__ == "__main__":
    # Set which pair we want to retrieve data for.
    pair = "SOL/USD"
    TIME_WINDOW = 60*300

    # NOTE: SOL inception date: roughly 2020-04-10 or epoch: 1586523600
    base_date = 1630717200 # Around the time the price exploded

    epoch_time = dt.datetime.utcnow().timestamp()

    # Fetch data in sliding window 60*300 seconds wide starting from current time
    # and sliding backward until the base date is reached.
    while epoch_time > base_date:
        print(f"fetching from: {epoch_time} to {epoch_time-TIME_WINDOW}")
        fetch_data(symbol=pair,
                start=dt.datetime.fromtimestamp(epoch_time-TIME_WINDOW).isoformat(),
                end=dt.datetime.fromtimestamp(epoch_time).isoformat())

        epoch_time -= TIME_WINDOW
        time.sleep(5)
