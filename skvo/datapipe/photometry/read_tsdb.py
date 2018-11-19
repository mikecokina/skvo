import logging
from datetime import datetime

import pandas as pd
from pyopentsdb import tsdb

from conf import config as gconf
from datapipe.photometry import transform as ptransform
from observation import transform as mdptransform  # model dependent transform
from utils import time_utils as tu
from utils.special_characters import special_characters_encode

logger = logging.getLogger('datapipe.photometry.read_tsdb')
dtype = "photometry"


def check_version(version):
    if version is None:
        raise (TypeError, "missing 1 required positional argument: 'version' (float)")


def get_observation(version):
    check_version(version)


def get_error(version):
    check_version(version)


def get_oid(version):
    check_version(version)


def get_exposure(version):
    check_version(version)


def get_data(tsdb_connector: tsdb.TsdbConnector, target: str, instrument_hash: str, bandpass_uid: str,
             source: str, observation_id: int, start_date: datetime, end_date: datetime,
             max_tsdb_subqueries: int = 10, version: float = None):
    check_version(version)
    max_tsdb_subqueries = 1

    def _query_chunks(metrics_sequence, query_base):
        # todo: make it better
        chunks = [[
            dict(
                **{
                    "aggregator": 'none',
                    "metric": _metric,
                    "filters": [
                        {
                            "type": "literal_or",
                            "tagk": "target",
                            "filter": special_characters_encode(target),
                            "groupBy": False
                        },
                        {
                            "type": "literal_or",
                            "tagk": "instrument",
                            "filter": str(instrument_hash),
                            "groupBy": False
                        },
                        {
                            "type": "literal_or",
                            "tagk": "source",
                            "filter": str(source),
                            "groupBy": False
                        }
                    ]
                }
            )
            for _metric in chunk
        ]
            for chunk in list(metrics_sequence[i:i + max_tsdb_subqueries]
                              for i in range(0, len(metrics_sequence), max_tsdb_subqueries))
        ]

        queries = list()
        for chunk in chunks:
            query_dict = query_base.copy()
            query_dict["metrics"] = chunk
            queries.append(query_dict)
        return queries

    regexp = '([a-zA-Z0-9\-])\.{dtype}(.*)\.{version}$'.format(dtype=dtype, version=version)
    q = "{}.{}".format(special_characters_encode(target), special_characters_encode(bandpass_uid))
    suggested_metrics = sorted(tsdb_connector.metrics(q=q, regexp=regexp, max=10000))

    query_kwargs = gconf.OPENTSDB_QUERY.copy()
    query_kwargs.update(dict(start=start_date, end=end_date))
    query_chunks = _query_chunks(suggested_metrics, query_kwargs)

    tsdb_response = tsdb_connector.multiquery(query_chunks)
    df = ptransform.data_tsdb_reposne_to_df(tsdb_response) if tsdb_response else pd.DataFrame()
    df = df[df["observation_id"] == observation_id]
    data = mdptransform.photometry_data_df_to_dict(df)
    return data


def get_samples(tsdb_connector: tsdb.TsdbConnector, metadata: list, version: float = None):
    check_version(version)

    query_chunks = list()
    for meta in metadata:
        metric = ptransform.get_observation_id_tsdb_metric_name(meta["target"], meta["bandpass"])
        suggested_metric = tsdb_connector.metrics(q=metric, max=1)

        if not suggested_metric:
            logger.warning("It seems, OpenTSDB doesn' contain any records for metadata: {}".format(meta))
            continue

        query_kwargs = gconf.OPENTSDB_QUERY.copy()
        metrics = [
            dict(
                aggregator="zimsum",
                metric=suggested_metric[0],
                downsample="0all-count-none",
                filters=[
                    {
                        "type": "literal_or",
                        "filter": str(meta["instrument_hash"]),
                        "tagk": "instrument",
                        "groupBy": True
                    },
                    {
                        "type": "literal_or",
                        "filter": str(meta["source"]),
                        "tagk": "source",
                        "groupBy": True
                    },
                    {
                        "type": "literal_or",
                        "filter": special_characters_encode(str(meta["target"])),
                        "tagk": "target",
                        "groupBy": True
                    }
                ]
            )
        ]

        query_kwargs.update(dict(
            start=meta["start_date"],
            end=meta["end_date"],
            metrics=metrics
        ))
        query_chunks.append(query_kwargs)

    tsdb_response = tsdb_connector.multiquery(query_chunks=query_chunks)
    samples_info = ptransform.sample_tsdb_response_to_df(tsdb_response)

    # cleanup this shitcode
    samples_info_df = pd.DataFrame.from_dict(samples_info)
    samples_info_df["start_date"] = tu.unix_timestamp_to_pd(samples_info_df["start_date"], unit="ms")
    samples_info_df["start_date"] = tu.add_timezone_to_pd_series(samples_info_df["start_date"], 'UTC')
    samples_info_df["instrument_hash"] = samples_info_df["instrument_hash"].astype(str)
    samples_info_df["target"] = samples_info_df["target"].astype(str)
    samples_info_df["source"] = samples_info_df["source"].astype(str)
    samples_info_df["bandpass"] = samples_info_df["bandpass"].astype(str)

    metadata_df = pd.DataFrame.from_dict(metadata)
    metadata_df["instrument_hash"] = metadata_df["instrument_hash"].astype(str)
    metadata_df["target"] = metadata_df["target"].astype(str)
    metadata_df["source"] = metadata_df["source"].astype(str)
    metadata_df["bandpass"] = metadata_df["bandpass"].astype(str)

    samples_df = pd.merge(samples_info_df, metadata_df, how="outer",
                          left_on=["start_date", "instrument_hash", "target", "source", "bandpass"],
                          right_on=["start_date", "instrument_hash", "target", "source", "bandpass"])
    samples = mdptransform.photometry_samples_df_to_dict(samples_df)
    return samples
