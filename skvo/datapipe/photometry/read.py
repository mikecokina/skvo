import pandas as pd


def read_csv_file(path, encoding="utf8"):
    return pd.read_csv(path, encoding=encoding)
