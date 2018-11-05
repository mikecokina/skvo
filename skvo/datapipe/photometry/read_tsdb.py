from datetime import datetime
from pyopentsdb import tsdb
from conf import config
from datapipe.photometry import transform

import logging
logger = logging.getLogger('datapipe.photometry.read_tsdb')


def check_version(version):
    if version is None:
        raise (TypeError, "missing 1 required positional argument: 'version' (float)")


def get_data(tsdb_connector: tsdb.TsdbConnector, target: str,start_date: datetime, end_date: datetime=None,
             downsample: str = None, aggregator: str = None, max_tsdb_subqueries: int = 10,
             max_tsdb_concurrency: int = 20, version: float=None):
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


def get_samples(tsdb_connector: tsdb.TsdbConnector, metadata: list, max_tsdb_concurrency: int = 20, version: float=None):
    check_version(version)
    dtype = "photometry"

    query_chunks = list()
    for meta in metadata:

        regexp=transform.get_observation_id_tsdb_metric_name(meta["target"], meta["bandpass"])
        logger.info(regexp)
        # suggested_metric = tsdb_connector.metrics()

        query_kwargs = config.OPENTSDB_QUERY.copy()
        metrics = [
            dict(
                aggregators="zimsum",
                metric="x",
                downsample="0all-count-none",
                filters=[{
                    "type": "literal_or",
                    "filter": str(meta["instrument_uuid"]),
                    "tagk": "instrument",
                    "groupBy": True
                }]
            )
        ]

        query_kwargs.update(dict(
            start=meta["start_date"],
            end=meta["end_date"],
            metrics=metrics
        ))
        query_chunks.append(query_kwargs)
