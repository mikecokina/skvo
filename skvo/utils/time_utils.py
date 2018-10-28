from collections import Iterable

import numpy as np
import pandas as pd

from conf.config import TIMESTAMP_PARSING_COLUMNS


def _to_array(iterable_or_scalar):
    # we use object dtype in order to allow int64 and np.nan in single array
    # otherwise ints are converted to float64 with precision loss
    if isinstance(iterable_or_scalar, Iterable):
        return pd.Series(iterable_or_scalar, dtype=np.dtype('object')).values
    else:
        return pd.Series([iterable_or_scalar]).values


def _dt_to_array(iterable_or_scalar):
    # this is split from above due to precision
    # (whe we select object dtype timestamps are rounded to us)
    if isinstance(iterable_or_scalar, Iterable):
        return pd.Series(iterable_or_scalar).values
    else:
        return pd.Series([iterable_or_scalar]).values


def _array_to_orig_type(np_array, original_argument):
    original_type = type(original_argument)
    # scalar value
    if not isinstance(original_argument, Iterable):
        return pd.Series(np_array).iloc[0]
    # numpy array
    elif original_type == pd.np.ndarray:
        return np_array
    # series (set index)
    elif original_type == pd.Series:
        series = pd.Series(np_array, index=original_argument.index)
        return series
    # list
    elif original_type == list:
        return list(pd.Series(np_array))
    # we don't support anything else, return the array
    else:
        return np_array


def unix_timestamp_to_pd(unix_timestamp, unit='ns'):
    """
    convert unix timestamp to pd

    :param unix_timestamp: array / series / list or scalar of int (and possibly nans)
    :param unit: ('ns', 'ms) precision that timestamps were rounded to
    :return:
    """
    # convert to array
    unix_ts_arr = _to_array(unix_timestamp)
    # timestamps conversion
    pd_timestamp_arr = pd.np.empty(unix_ts_arr.shape, dtype='datetime64[ns]')
    not_null = pd.notnull(unix_ts_arr)
    not_null_unix_timestamp = unix_ts_arr[not_null].astype('int64')
    pd_timestamp_arr[not_null] = pd.to_datetime(not_null_unix_timestamp, unit=unit).values
    pd_timestamp_arr[~not_null] = pd.np.datetime64('nat')
    # convert back
    pd_timestamp = _array_to_orig_type(pd_timestamp_arr, unix_timestamp)
    return pd_timestamp


def pd_timestamp_to_unix(pd_timestamp, unit='ns'):
    """
    convert pd timestamps to unix

    :param pd_timestamp: array / series / list or scalar of pd.Timestamp
    :param unit: ('ns', 'ms') precision that timestamps should be rounded to
    """
    # convert to array
    pd_timestamp_arr = _dt_to_array(pd_timestamp)
    # timestamps conversion
    unix_timestamp_arr = pd.np.empty(pd_timestamp_arr.shape, dtype='object')
    not_null = pd.notnull(pd_timestamp_arr)
    not_null_pd_timestamps = pd_timestamp_arr[not_null].astype('datetime64[ns]')
    unix_timestamp_arr[not_null] = not_null_pd_timestamps.astype('int64')
    if unit == 'ms':
        unix_timestamp_arr[not_null] //= 10**6

    unix_timestamp_arr[~not_null] = pd.np.nan
    # convert back
    unix_timestamp = _array_to_orig_type(unix_timestamp_arr, pd_timestamp)
    return unix_timestamp


def unix_timestamp_to_tsdb(unix_timestamp, unit='ns'):
    """
    convert unix timestamp to tsdb compatible (timestamps to milliseconds)

    :param unix_timestamp: array / series / list or scalar of int
    :param unit: ('ns', 'ms') precision of unix_timestamp input
    """
    pd_ts = unix_timestamp_to_pd(unix_timestamp, unit=unit)
    tsdb_ts = pd_timestamp_to_unix(pd_ts, unit='ms')
    return tsdb_ts


def parse_timestamp(df):
    """
    Extract single timestamp series from data

    :param df: pandas.DataFrame
    :return: pandas.Series of pandas.Timestamp
    """
    timestamp = pd.Series(dtype=np.dtype('<M8[ns]'), index=df.index)
    for time_col in TIMESTAMP_PARSING_COLUMNS:
        if timestamp.hasnans and time_col in df:
            dt_series = df[time_col]
            if dt_series.dtype not in (np.dtype('<M8[ns]'), np.dtype('datetime64[ns]')):
                dt_series = pd.to_datetime(dt_series, errors='coerce')
            timestamp.loc[timestamp.isnull()] = dt_series.loc[timestamp.isnull()]
    return timestamp
