import logging
import requests
import json

from abc import ABCMeta, abstractmethod

import time
from pyopentsdb import tsdb

# def imp(validated_data):
#     # todo: add importer logic here
#     return True


class AbstractHttpImporter(metaclass=ABCMeta):

    @abstractmethod
    def imp(self, *args, **kwargs):
        pass


class OpenTsdbHttpImporter(AbstractHttpImporter):
    def __init__(self, server, batch_size, **kwargs):
        self._logger = logging.getLogger(OpenTsdbHttpImporter.__name__)
        self._server = server
        self._batch_size = batch_size
        self._session = requests.Session()
        self._tsdb_connector = tsdb.tsdb_connection(host=self._server)

    @property
    def server(self):
        return self._server

    @property
    def tsdb_api(self):
        return "{}".format(self._server)

    def batch_split(self, metrics):
        for i in range(0, len(metrics), self._batch_size):
            yield metrics[i:i + self._batch_size]

    def http_send(self, batch):
        start_time = time.time()
        end_time = time.time() + 0.000001
        speed = len(batch) / (end_time - start_time)
        self._logger.info("Imported {} metrics, speed {} metrics/s".format(len(batch), speed))
        try:
            self._tsdb_connector.put(data=batch)
        except Exception as e:
            self._logger.error("Cannot send data to OpenTSDB due to: {}".format(str(e)))
            raise

    def imp(self, metrics):
        if isinstance(metrics, dict):
            metrics = [metrics]
        metrics = self.batch_split(metrics)
        for metric_batch in metrics:
            self.http_send(metric_batch)


class MetadataHttpImporter(AbstractHttpImporter):
    def __init__(self, server, **kwargs):
        self._logger = logging.getLogger(OpenTsdbHttpImporter.__name__)
        self._server = server
        self._session = requests.Session()

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def api_endpoint(self):
        return "{}/api/photometry/metadata/".format(self._server)

    def imp(self, json_data):
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }
        r = self._session.post(self.api_endpoint, data=json.dumps(json_data), headers=headers)
        self._session.close()
        return r


class MediaHttpImporter(AbstractHttpImporter):
    def __init__(self, server):
        self._server = server
        self._session = requests.Session()

    @property
    def server(self):
        return self._server

    @property
    def api_endpoint(self):
        return "{}/api/photometry/media/".format(self._server)

    def imp(self, raw_data, filename):
        headers = {
            'Content-Type': 'multipart/form-data',
            'Content-Disposition': 'attachment; filename = "{}'.format(filename),
        }
        r = self._session.post(self.api_endpoint, data=raw_data, headers=headers)
        self._session.close()
        return r
