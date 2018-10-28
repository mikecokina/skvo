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

    metrics = [
        {
            'metric': get_tsdb_metric_name(df["target.catalogue_value"].iloc[i],
                                           df["bandpass.bandpass_uid"].iloc[i]),
            'timestamp': timestamp.iloc[i],
            'value': df["ts.magnitude"].iloc[i],
            'tags':
                {
                    'instrument': source,
                    'target': df["target.target"].iloc[0],
                    'source': source
                }
        }
        for i in range(timestamp.shape[0])
    ]

    return metrics


def photometry_data_df_to_tsdb_meta_metrics(df, source):
    df.reset_index(inplace=True, drop=True)
    df_timestamp = time_utils.parse_timestamp(df)
    timestamp = time_utils.pd_timestamp_to_unix(df_timestamp, unit='ms')

    metrics = [
        {
            'metric': get_tsdb_metric_name(df["target.catalogue_value"].iloc[i],
                                           df["bandpass.bandpass_uid"].iloc[i]),
            'timestamp': timestamp.iloc[i],
            'value': df["ts.magnitude"].iloc[i],
            'tags':
                {
                    'instrument': source,
                    'target': df["target.target"].iloc[0],
                    'source': source,
                    'bandpass': df["bandpass.bandpass_uid"].iloc[i]
                }
        }
        for i in range(timestamp.shape[0])
    ]

    return metrics


def photometry_data_to_metadata_json(metadata_df, data_df, source):
    df = data_df.copy()
    df_timestamp = time_utils.parse_timestamp(df)
    timestamp = time_utils.pd_timestamp_to_unix(df_timestamp, unit='ms')
    df["ts.unix"] = timestamp

    metadata = dict(
        # todo: prepare json like in serializers header
        start_date=df["ts.timestamp"][df.first_valid_index()],
        end_date=df["ts.timestamp"][df.last_valid_index()],
    )

    return metadata


def photometry_media_to_import_json(media_content, filename, data, metadata, source):
    import_json = {
        "content": media_content,
        "filename": filename,
        "source": source,
        "bandpass": None
    }

    return import_json
