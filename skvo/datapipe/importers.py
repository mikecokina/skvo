import logging
import requests
import json

from abc import ABCMeta, abstractmethod

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

    @property
    def server(self):
        return self._server

    @property
    def tsdb_api(self):
        return "{}".format(self._server)

    def batch_split(self):
        pass

    def http_send(self):
        pass

    def imp(self, metrics):
        pass


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
        return "{}://{}:{}/api/metadata".format(self._protocol, self._host, self._port)

    def imp(self, json_data):
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }
        r = self._session.post(self.api_endpoint, data=json.dumps(json_data), headers=headers)
        return r


class MediaHttpImporter(AbstractHttpImporter):
    def __init__(self, server):
        self._server = server

    @property
    def server(self):
        return self._server

    def imp(self, content_json):
        pass
