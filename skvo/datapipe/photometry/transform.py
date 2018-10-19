from datapipe.photometry import config as photometry_config
from utils.special_characters import special_characters_encode
from utils import time_utils



def prepare_message():
    pass


def get_photometry_loader(transform=None, init_sink=None):

    def load_photometry(start_date=None, end_date=None, **kwargs):
        sink = init_sink(**kwargs)
        sink()
    return load_photometry


def join_photometry_data(data, metadata):
    df = data.copy()
    meta_columns = metadata.columns
    for column in meta_columns:
        if column not in df:
            df[column] = metadata[column].iloc[0]
        else:
            raise ValueError("metadata dataframe contain same column name as observation data dataframe")
    return df


def get_tsdb_metric_name(target_catalogue_value, bandpass_uid):
    suffix = photometry_config.TSDB_METRIC_SUFFIX
    target_uid = special_characters_encode(target_catalogue_value)
    bandpass_uid = special_characters_encode(bandpass_uid)
    return '{}.{}.{}'.format(target_uid, bandpass_uid, suffix)


def photometry_data_df_to_tsdb_metrics(df, source):
    df.reset_index(inplace=True, drop=True)
    df_timestamp = time_utils.parse_timestamp(df)
    timestamp = time_utils.pd_timestamp_to_unix(df_timestamp, unit='ms')

    for i in range(df.shape[0]):
        print(get_tsdb_metric_name(df["target.catalogue_value"].iloc[i],
                                   df["bandpass.bandpass_uid"].iloc[i]))
    # metrics = [
    #     {
    #         'metric': metric_names[col],
    #         'timestamp': int(ts),
    #         'value': val,
    #         'tags':
    #             {
    #                 'source': source,
    #                 'type': 'analog',
    #                 'package': package_sn,
    #                 'tag_name': _get_metric_tag_name(col)
    #             }
    #     }
    #     for col in value_columns
    #     for ts, val, is_valid in zip(timestamp.values, df[col], is_valid_tsdb_series(df[col])) if is_valid
    # ]
    #
    # return TsdbMetric(metrics, source, package_sn)
    pass
