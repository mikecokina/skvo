import logging
import requests
import json


# def imp(validated_data):
#     # todo: add importer logic here
#     return True


class OpenTsdbHttpImporter(object):
    def __init__(self, host, port, protocol, batch_size, **kwargs):
        self._logger = logging.getLogger(OpenTsdbHttpImporter.__name__)
        self._host = host
        self._port = port
        self._protocol = protocol
        self._batch_size = batch_size
        self._session = requests.Session()

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def tsdb_api(self):
        return "{}://{}:{}".format(self._protocol, self._host, self._port)

    def send(self):
        pass


class MetadataHttpImporter(object):
    def __init__(self, host, port, protocol, **kwargs):
        self._logger = logging.getLogger(OpenTsdbHttpImporter.__name__)
        self._host = host
        self._port = port
        self._protocol = protocol
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
