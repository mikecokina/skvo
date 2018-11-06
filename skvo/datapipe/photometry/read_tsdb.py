import logging
from datetime import datetime

import pandas as pd
from pyopentsdb import tsdb

from conf import config
from datapipe.photometry import transform
from utils import time_utils as tu

logger = logging.getLogger('datapipe.photometry.read_tsdb')


def check_version(version):
    if version is None:
        raise (TypeError, "missing 1 required positional argument: 'version' (float)")


def get_data(tsdb_connector: tsdb.TsdbConnector, target: str, start_date: datetime, end_date: datetime = None,
             downsample: str = None, aggregator: str = None, max_tsdb_subqueries: int = 10,
             max_tsdb_concurrency: int = 20, version: float = None):
    check_version(version)
    dtype = "photometry"

    def _query_chunks(metrics_sequence, query_base):
        # todo: make it better
        chunks = [[
            dict(**{
                "aggregator": aggregator or 'none',
                "metric": _metric,
                "filters": [{
                    "type": "literal_or",
                    "tagk": "target",
                    "filter": str(target),
                    "groupBy": False
                }]
            }, **({"downsample": downsample} if downsample else dict())
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

    regexp = '([a-zA-Z0-9\-])\.{dtype}\.v{version}$'.format(dtype=dtype, version=version)
    suggested_metrics = sorted(tsdb_connector.metrics(q=target, regexp=regexp, max=10000))

    query_kwargs = config.OPENTSDB_QUERY.copy()
    query_kwargs.update(dict(start=start_date, end=end_date))

    query_chunks = _query_chunks(suggested_metrics, query_kwargs)

    logger.info(query_chunks)


def get_samples(tsdb_connector: tsdb.TsdbConnector, metadata: list, max_tsdb_concurrency: int = 20,
                version: float = None):
    check_version(version)
    dtype = "photometry"

    query_chunks = list()
    for meta in metadata:
        metric = transform.get_observation_id_tsdb_metric_name(meta["target"], meta["bandpass"])
        suggested_metric = tsdb_connector.metrics(q=metric, max=1)

        if not suggested_metric:
            logger.warning("It seems, OpenTSDB doesn' contain any records for metadata: {}".format(meta))
            continue

        query_kwargs = config.OPENTSDB_QUERY.copy()
        metrics = [
            dict(
                aggregator="zimsum",
                metric=suggested_metric[0],
                downsample="0all-count-none",
                filters=[
                    {
                        "type": "literal_or",
                        "filter": str(meta["instrument_uuid"]),
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
                        "filter": str(meta["target"]),
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
    samples_info = transform.sample_tsdb_response_to_df(tsdb_response)

    # cleanup this shitcode
    samples_info_df = pd.DataFrame.from_dict(samples_info)
    samples_info_df["start_date"] = tu.unix_timestamp_to_pd(samples_info_df["start_date"], unit="ms")
    samples_info_df["start_date"] = tu.add_timezone_to_pd_series(samples_info_df["start_date"], 'UTC')
    samples_info_df["instrument_uuid"] = samples_info_df["instrument_uuid"].astype(str)
    samples_info_df["target"] = samples_info_df["target"].astype(str)
    samples_info_df["source"] = samples_info_df["source"].astype(str)
    samples_info_df["bandpass"] = samples_info_df["bandpass"].astype(str)

    metadata_df = pd.DataFrame.from_dict(metadata)
    metadata_df["instrument_uuid"] = metadata_df["instrument_uuid"].astype(str)
    metadata_df["target"] = metadata_df["target"].astype(str)
    metadata_df["source"] = metadata_df["source"].astype(str)
    metadata_df["bandpass"] = metadata_df["bandpass"].astype(str)

    samples_df = pd.merge(samples_info_df, metadata_df, how="outer",
                          left_on=["start_date", "instrument_uuid", "target", "source", "bandpass"],
                          right_on=["start_date", "instrument_uuid", "target", "source", "bandpass"])
    samples = transform.samples_df_to_dict(samples_df)
    return samples
