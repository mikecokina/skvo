import datetime
import json

import os
import requests

from conf import config
from datapipe.photometry import config as photometry_config
from skvo import settings
from utils import time_utils
from utils.special_characters import special_characters_encode


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


def preprocess_photometry_joined_df(joined_df):
    joined_df.reset_index(inplace=True, drop=True)
    df_timestamp = time_utils.parse_timestamp(joined_df)
    timestamp = time_utils.pd_timestamp_to_unix(df_timestamp, unit='ms')
    return joined_df, timestamp


def preprocess_tsdb_metric_keys(target_catalogue_value, bandpass_uid):
    suffix = photometry_config.TSDB_METRIC_SUFFIX
    target_uid = special_characters_encode(target_catalogue_value)
    bandpass_uid = special_characters_encode(bandpass_uid)
    return target_uid, bandpass_uid, suffix


def get_observation_tsdb_metric_name(target_catalogue_value, bandpass_uid):
    target_uid, bandpass_uid, suffix = preprocess_tsdb_metric_keys(target_catalogue_value, bandpass_uid)
    return '{}.{}.{}'.format(target_uid, bandpass_uid, suffix)


def get_observation_id_tsdb_metric_name(target_catalogue_value, bandpass_uid):
    target_uid, bandpass_uid, suffix = preprocess_tsdb_metric_keys(target_catalogue_value, bandpass_uid)
    return '{}.{}.{}.{}'.format(target_uid, bandpass_uid, "observation_id", suffix)


def get_exposure_tsdb_metric_name(target_catalogue_value, bandpass_uid):
    target_uid, bandpass_uid, suffix = preprocess_tsdb_metric_keys(target_catalogue_value, bandpass_uid)
    return '{}.{}.{}.{}'.format(target_uid, bandpass_uid, "exposure", suffix)


def get_error_tsdb_metric_name(target_catalogue_value, bandpass_uid):
    target_uid, bandpass_uid, suffix = preprocess_tsdb_metric_keys(target_catalogue_value, bandpass_uid)
    return '{}.{}.{}.{}'.format(target_uid, bandpass_uid, "error", suffix)


def df_to_timeseries_tsdb_metrics(df, source):
    df, timestamp = preprocess_photometry_joined_df(df)

    return [
        {
            'metric': get_observation_tsdb_metric_name(df["target.catalogue_value"].iloc[i],
                                                       df["bandpass.bandpass_uid"].iloc[i]),
            'timestamp': int(timestamp.iloc[i]),
            'value': float(df["ts.magnitude"].iloc[i]),
            'tags':
                {
                    'instrument': str(df["instrument.instrument"].iloc[0]),
                    'target': str(df["target.target"].iloc[0]),
                    'source': str(source),
                    'flux_calibration_level': int(df["ts.flux_calibration_level"].iloc[i]),
                    'flux_calibration': str(df["ts.flux_calibration"].iloc[i]),
                    'timeframe_reference_possition': str(df["ts.timeframe_reference_position"].iloc[i])
                }
        }
        for i in range(timestamp.shape[0])
    ]


def observation_id_data_df_to_tsdb_metrics(df, source, observation_id):
    df, timestamp = preprocess_photometry_joined_df(df)
    return [
        {
            'metric': get_observation_id_tsdb_metric_name(df["target.catalogue_value"].iloc[i],
                                                          df["bandpass.bandpass_uid"].iloc[i]),
            'timestamp': int(timestamp.iloc[i]),
            'value': int(observation_id),
            'tags':
                {
                    'instrument': str(df["instrument.instrument"].iloc[0]),
                    'target': str(df["target.target"].iloc[0]),
                    'source': str(source)
                }
        }
        for i in range(timestamp.shape[0])
    ]


def df_to_exposure_tsdb_metrics(df, source):
    df, timestamp = preprocess_photometry_joined_df(df)
    return [
        {
            'metric': get_exposure_tsdb_metric_name(df["target.catalogue_value"].iloc[i],
                                                    df["bandpass.bandpass_uid"].iloc[i]),
            'timestamp': int(timestamp.iloc[i]),
            'value': int(df["ts.exposure"].iloc[i]),
            'tags':
                {
                    'instrument': str(df["instrument.instrument"].iloc[0]),
                    'target': str(df["target.target"].iloc[0]),
                    'source': str(source),

                }
        }
        for i in range(timestamp.shape[0])
    ]


def df_to_errors_tsdb_metrics(df, source):
    df, timestamp = preprocess_photometry_joined_df(df)
    return [
        {
            'metric': get_exposure_tsdb_metric_name(df["target.catalogue_value"].iloc[i],
                                                    df["bandpass.bandpass_uid"].iloc[i]),
            'timestamp': int(timestamp.iloc[i]),
            'value': float(df["ts.magnitude_error"].iloc[i]),
            'tags':
                {
                    'instrument': str(df["instrument.instrument"].iloc[0]),
                    'target': str(df["target.target"].iloc[0]),
                    'source': str(source)
                }
        }
        for i in range(timestamp.shape[0])
    ]


def photometry_data_to_metadata_json(metadata_df, data_df, source):
    df = data_df.copy()
    df_timestamp = time_utils.parse_timestamp(df)
    timestamp = time_utils.pd_timestamp_to_unix(df_timestamp, unit='ms')
    df["ts.unix"] = timestamp
    start_date = datetime.datetime.strptime(df["ts.timestamp"][df.first_valid_index()], "%Y-%m-%d %H:%M:%S")

    metadata = \
        {
            "photometry": [
                {
                    "observation": {
                        "access": {
                            "access": metadata_df["access.access"].iloc[0]
                        },
                        "target": {
                            "target": metadata_df["target.target"].iloc[0],
                            "catalogue": metadata_df["target.catalogue"].iloc[0],
                            "catalogue_value": metadata_df["target.catalogue_value"].iloc[0],
                            "description": metadata_df["target.description"].iloc[0],
                            "right_ascension": metadata_df["target.right_ascension"].iloc[0],
                            "declination": metadata_df["target.declination"].iloc[0],
                            "target_class": metadata_df["target.target_class"].iloc[0]
                        },
                        "instrument": {
                            "instrument": metadata_df["instrument.instrument"].iloc[0],
                            "instrument_uid": metadata_df["instrument.instrument_uid"].iloc[0],
                            "telescope": metadata_df["instrument.telescope"].iloc[0],
                            "camera": metadata_df["instrument.camera"].iloc[0] or None,
                            "spectroscope": metadata_df["instrument.spectroscope"].iloc[0] or None,
                            "field_of_view": metadata_df["instrument.field_of_view"].iloc[0],
                            "description": metadata_df["instrument.description"].iloc[0]
                        },
                        "facility": {
                            "facility": metadata_df["facility.facility"].iloc[0],
                            "facility_uid": metadata_df["facility.facility_uid"].iloc[0],
                            "description": metadata_df["facility.description"].iloc[0]
                        },
                        "dataid": {
                            "title": metadata_df["dataid.title"].iloc[0],
                            "source": source,
                            "publisher": metadata_df["dataid.publisher"].iloc[0],
                            "publisher_did": metadata_df["dataid.publisher_did"].iloc[0],
                            "organisation": {
                                "organisation": metadata_df["organisation.organisation"].iloc[0],
                                "organisation_did": metadata_df["organisation.organisation_did"].iloc[0],
                                "email": metadata_df["organisation.email"].iloc[0]
                            }
                        }
                    },
                    "start_date": df["ts.timestamp"][df.first_valid_index()],
                    "end_date": df["ts.timestamp"][df.last_valid_index()],
                    "bandpass": {
                        "bandpass": metadata_df["bandpass.bandpass"].iloc[0],
                        "bandpass_uid": metadata_df["bandpass.bandpass_uid"].iloc[0],
                        "spectral_band_type": metadata_df["bandpass.spectral_band_type"].iloc[0],
                        "photometric_system": metadata_df["bandpass.photometric_system"].iloc[0]
                    },
                    "media": os.path.join(
                        source, config.DTYPES_BASE_DIR["photometry"], "media",
                        datetime.datetime.strftime(start_date, "%Y%m"),
                        "{}_{}".format(metadata_df["target.target"].iloc[0],
                                       datetime.datetime.strftime(start_date, "%Y%m%d")),
                        metadata_df["bandpass.bandpass_uid"].iloc[0]
                    )
                }
            ]
        }

    return metadata


def photometry_media_to_import_json(media_content, filename, data, metadata, source):
    import_json = {
        "content": media_content,
        "filename": filename,
        "source": source,
        "bandpass": None
    }

    return import_json


def convert_df_float_values(df):
    for column in config.PHOTOMETRY_FLOAT_FIELDS:
        if column in df:
            df[column] = df[column].astype(float)
    return df


def convert_df_int_values(df):
    for column in config.PHOTOMETRY_INT_FIELDS:
        if column in df:
            df[column] = df[column].astype(int)
    return df


def get_response_observation_uuid(response: requests.Response):
    if response.status_code in [200, 201]:
        content = json.loads(response.content.decode())
        return content["photometry"][-1]["observation"]["observation_uuid"]
    raise ValueError("Unexpected response status code")


def get_response_observation_id(response: requests.Response):
    if response.status_code in [200, 201]:
        content = json.loads(response.content.decode())
        return content["photometry"][-1]["observation"]["id"]
    raise ValueError("Unexpected response status code")
