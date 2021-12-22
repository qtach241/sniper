import os
import pandas

"""
This utility takes the output of data_utils.py (a CSV file), reorders
the items in ascending order, and writes it to a new file.
"""

if __name__ == "__main__":
    # Enter input filename here:
    filename = 'Coinbase_SOLUSD_data.csv'

    # Enter output filename here:
    out_filename = 'Coinbase_SOLUSD_data_sorted.csv'

    dir = os.path.dirname(__file__)
    file = os.path.join(dir, filename)

    df = pandas.read_csv(file)
    sorted_df = df.sort_values(by=['unix'], ascending=True)
    print(sorted_df)

    sorted_df.to_csv(out_filename, index=False)
