import datetime
import io
import itertools
import json
import os
import pandas as pd

import avro
import requests
from avro.io import DatumWriter

from conf import config
from datapipe import utils as dputils
from datapipe.photometry import config as photometry_config, filesystem
from utils import time_utils
from utils import utils
from utils.special_characters import special_characters_encode, special_characters_decode


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
    return '{}.{}.{}.{}'.format(target_uid, bandpass_uid, "oid", suffix)


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
                    'instrument': str(df["instrument.instrument_hash"].iloc[0]),
                    'target': special_characters_encode(str(df["target.target"].iloc[0])),
                    'source': str(source),
                    'flux_calibration_level': int(df["ts.flux_calibration_level"].iloc[i]),
                    'flux_calibration': str(df["ts.flux_calibration"].iloc[i]),
                    'timeframe_reference_position': str(df["ts.timeframe_reference_position"].iloc[i]),
                    'dtype': 'observation'
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
                    'instrument': str(df["instrument.instrument_hash"].iloc[0]),
                    'target': special_characters_encode(str(df["target.target"].iloc[0])),
                    'source': str(source),
                    'dtype': 'oid'
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
                    'instrument': str(df["instrument.instrument_hash"].iloc[0]),
                    'target': special_characters_encode(str(df["target.target"].iloc[0])),
                    'source': str(source),
                    'dtype': 'exposure'

                }
        }
        for i in range(timestamp.shape[0])
    ]


def df_to_errors_tsdb_metrics(df, source):
    df, timestamp = preprocess_photometry_joined_df(df)
    return [
        {
            'metric': get_error_tsdb_metric_name(df["target.catalogue_value"].iloc[i],
                                                 df["bandpass.bandpass_uid"].iloc[i]),
            'timestamp': int(timestamp.iloc[i]),
            'value': float(df["ts.magnitude_error"].iloc[i]),
            'tags':
                {
                    'instrument': str(df["instrument.instrument_hash"].iloc[0]),
                    'target': special_characters_encode(str(df["target.target"].iloc[0])),
                    'source': str(source),
                    'dtype': 'error'
                }
        }
        for i in range(timestamp.shape[0])
    ]


def compute_sha512_from_metadata(metadata, salt):
    metadata = metadata.sort_index(axis=1)
    values = str(salt) + "___" + "___".join([str(metadata[col].iloc[0]) for col in metadata.columns])
    return utils.sha512_content(str(values).encode('utf-8'))


def compute_md5_from_metadata(metadata, salt):
    metadata = metadata.sort_index(axis=1)
    values = str(salt) + "___" + "___".join([str(metadata[col].iloc[0]) for col in metadata.columns])
    return utils.md5_raw_content(str(values).encode('utf-8'))


def compute_metadata_md5(order, separator, **kwargs):
    return utils.md5_raw_content(str(separator).join([str(kwargs[k]) for k in order]).encode('utf-8'))


def photometry_data_to_metadata_json(metadata_df, data_df, source):
    df = data_df.copy()
    df_timestamp = time_utils.parse_timestamp(df)
    timestamp = time_utils.pd_timestamp_to_unix(df_timestamp, unit='ms')
    df["ts.unix"] = timestamp
    df = df.sort_values("ts.unix")
    df = df.reset_index(drop=True)
    start_date = datetime.datetime.strptime(df["ts.timestamp"][df.first_valid_index()], "%Y-%m-%d %H:%M:%S")
    observation_hash = compute_md5_from_metadata(metadata_df, datetime.datetime.strftime(start_date, "%Y%m%d"))
    instrument = {
        "instrument": metadata_df["instrument.instrument"].iloc[0],
        "telescope": metadata_df["instrument.telescope"].iloc[0],
        "camera": metadata_df["instrument.camera"].iloc[0] or None,
        "spectroscope": metadata_df["instrument.spectroscope"].iloc[0] or None,
        "field_of_view": metadata_df["instrument.field_of_view"].iloc[0],
        "description": metadata_df["instrument.description"].iloc[0]
    }
    instrument_hash = compute_metadata_md5(
        order=["instrument", "telescope", "camera", "spectroscope", "field_of_view"],
        separator="___",
        **instrument

    )

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
                            "target_class": metadata_df["target.target_class"].iloc[0],
                            "equinox": metadata_df["target.equinox"].iloc[0]
                        },
                        "instrument": dict(instrument_hash=instrument_hash, **instrument),
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
                        },
                        "observation_hash": observation_hash
                    },
                    "start_date": df["ts.timestamp"][df.first_valid_index()],
                    "end_date": df["ts.timestamp"][df.last_valid_index()],
                    "bandpass": {
                        "bandpass": metadata_df["bandpass.bandpass"].iloc[0],
                        "bandpass_uid": metadata_df["bandpass.bandpass_uid"].iloc[0],
                        "spectral_band_type": metadata_df["bandpass.spectral_band_type"].iloc[0],
                        "photometric_system": metadata_df["bandpass.photometric_system"].iloc[0]
                    },
                    "media": str(os.path.join(
                        source, config.DTYPES_BASE_DIR["photometry"], "media",
                        datetime.datetime.strftime(start_date, "%Y%m"),
                        "{}_{}".format(metadata_df["target.target"].iloc[0],
                                       datetime.datetime.strftime(start_date, "%Y%m%d")),
                        metadata_df["bandpass.bandpass_uid"].iloc[0]
                    )).replace(os.sep, '::os.sep::')
                }
            ]
        }

    return metadata


def avro_msg_serializer(media_content, filename, metadata_df, data_df, source, md5_crc):
    df = data_df.copy()
    df_timestamp = time_utils.parse_timestamp(df)
    timestamp = time_utils.pd_timestamp_to_unix(df_timestamp, unit='ms')
    df["ts.unix"] = timestamp
    df = df.sort_values("ts.unix")
    df = df.reset_index(drop=True)
    start_date = df["ts.timestamp"][df.first_valid_index()]
    mediafile_index = int(filesystem.get_file_part_index(filename))
    mediafile_suffix = df["ts.unix"].iloc[mediafile_index]
    filename, file_extension = os.path.splitext(filename)
    filename = "{}___{}{}".format(filename, mediafile_suffix, file_extension)

    import_json = {
        "content": media_content,
        "filename": filename,
        "target": metadata_df["target.target"].iloc[0],
        "md5_crc": md5_crc,
        "source": source,
        "bandpass": metadata_df["bandpass.bandpass_uid"].iloc[0],
        "start_date": start_date
    }
    return import_json


def avro_raw_deserializer(avro_decoded_data):
    return {
        "content": avro_decoded_data["content"],
        "filename": avro_decoded_data["filename"],
        "target": avro_decoded_data["target"],
        "md5_crc": avro_decoded_data["md5_crc"],
        "source": avro_decoded_data["source"],
        "bandpass": avro_decoded_data["bandpass"],
        "start_date": datetime.datetime.strptime(avro_decoded_data["start_date"], "%Y-%m-%d %H:%M:%S")
    }


def get_media_avro_path():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'avsc', 'photometry_media.avsc'
    )


def get_media_avro_schema():
    with open(get_media_avro_path(), 'r') as f:
        return avro.schema.Parse(f.read())


def encode_avro_message(data):
    datum_writer = DatumWriter(get_media_avro_schema())
    bytes_writer = io.BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    datum_writer.write(data, encoder)
    raw_bytes = bytes_writer.getvalue()
    return raw_bytes


def decode_avro_message(bytes_reader):
    # bytes_reader = io.BytesIO(msg)
    # bytes_reader = in_memory_uploaded_file.read()
    decoder = avro.io.BinaryDecoder(bytes_reader)
    reader = avro.io.DatumReader(get_media_avro_schema())
    decoded_values = reader.read(decoder)
    return decoded_values


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


def expand_metadata_with_instrument_hash(metadata_df, hash):
    metadata_df["instrument.instrument_hash"] = hash
    return metadata_df


def get_response_observation_id(response: requests.Response):
    if response.status_code in [200, 201]:
        content = json.loads(response.content.decode())
        return content["photometry"][-1]["observation"]["id"]
    raise ValueError("Unexpected response status code")


def get_response_instrument_hash(response: requests.Response):
    if response.status_code in [200, 201]:
        content = json.loads(response.content.decode())
        return content["photometry"][-1]["observation"]["instrument"]["instrument_hash"]
    raise ValueError("Unexpected response status code")


def sample_tsdb_response_to_df(tsdb_response):
    # there shouldn't be a case, when there is more values with sme instrument and start date
    # in real life you are not able observe in one time, same object one the sme instrument twice
    # in case of two nasmyth focus, each of them have to be marked with different instrument
    return [
        {
            "samples": int(list(metric["dps"].values())[0]),
            "start_date": int(list(metric["dps"].keys())[0]),
            "instrument_hash": metric["tags"]["instrument"],
            "source": metric["tags"]["source"],
            "target": metric["tags"]["target"],
            "bandpass": dputils.parse_bandpass_from_metric(metric["metric"])
        }
        for metric in tsdb_response
    ]


def add_separation_to_samples_dict(samples_dict):
    return samples_dict


def merge_observation_data(df1, df2):
    (left, right) = (df1, df2) if len(df1) > len(df2) else (df2, df1)
    return pd.merge(
        left, right, how='left', left_on=['timestamp'], right_on=['timestamp']
    )


def extract_observation_data(group):
    df = pd.DataFrame({"timestamp": list(group[0]["dps"].keys()),
                       "magnitude": list(group[0]["dps"].values())})

    df["timeframe_reference_position"] = group[0]["tags"]["timeframe_reference_position"]
    df["instrument"] = group[0]["tags"]["instrument"]
    df["source"] = group[0]["tags"]["source"]
    df["target"] = special_characters_decode(group[0]["tags"]["target"])
    df["flux_calibration"] = special_characters_decode(group[0]["tags"]["flux_calibration"])
    df["flux_calibration_level"] = special_characters_decode(group[0]["tags"]["flux_calibration_level"])
    df["bandpass"] = special_characters_decode(dputils.parse_bandpass_from_metric(group[0]["metric"]))

    df = df.sort_values("timestamp")
    return df


def extract_oid(group):
    df = pd.DataFrame({"timestamp": list(group[0]["dps"].keys()),
                       "observation_id": list(group[0]["dps"].values())})
    df = df.sort_values("timestamp")
    return df


def extract_error(group):
    df = pd.DataFrame({"timestamp": list(group[0]["dps"].keys()),
                       "error": list(group[0]["dps"].values())})
    df = df.sort_values("timestamp")
    return df


def extract_exposure(group):
    df = pd.DataFrame({"timestamp": list(group[0]["dps"].keys()),
                       "exposure": list(group[0]["dps"].values()),
                       })
    df = df.sort_values("timestamp")
    return df


def data_tsdb_reposne_to_df(tsdb_response):
    repository_groups = {key: list(group)
                         for key, group in itertools.groupby(tsdb_response, key=lambda x: x['metric'])}

    df = pd.DataFrame(columns=["timestamp"])

    oid_key = utils.find_key(repository_groups.keys(), ".oid.")
    oid_data = extract_oid(repository_groups.pop(oid_key))

    error_key = utils.find_key(repository_groups.keys(), ".error.")
    error_data = extract_error(repository_groups.pop(error_key))

    exposure_key = utils.find_key(repository_groups.keys(), ".exposure.")
    exposure_data = extract_exposure(repository_groups.pop(exposure_key))

    data = extract_observation_data(repository_groups.pop(list(repository_groups.keys())[0]))

    dfs = [oid_data, exposure_data, error_data, data]

    for _df in dfs:
        df = merge_observation_data(df, _df)
    return df
