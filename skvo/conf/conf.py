from configparser import ConfigParser
from logging import config as logconf

import os
import json
import logging
import warnings


parser = ConfigParser()
venv_config = os.path.join(os.environ.get('VIRTUAL_ENV', ''), 'conf', 'skvo.ini')

if not os.path.isfile(venv_config):
    raise LookupError("Couldn't resolve configuration file. To define it \n "
                      "  - add conf/skvo.ini under your virtualenv root\n")

CONFIG_FILE = venv_config
LOG_CONFIG = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf', 'skvo-log.json')

OPENTSDB_HOST = "localhost"
OPENTSDB_PORT = 4242
OPENTSDB_PROTOCOL = "http"
OPENTSDB_BATCH_SIZE = 10000


def set_up_logging():
    if os.path.isfile(LOG_CONFIG):
        with open(LOG_CONFIG) as f:
            conf_json = json.loads(f.read())
        logconf.dictConfig(conf_json)
    else:
        logging.basicConfig(level=logging.INFO)


def read_and_update_config(path=None):
    if not path:
        path = CONFIG_FILE

    if not os.path.isfile(path):
        msg = (
            "Couldn't find configuration file. Using default settings.\n"
        )
        warnings.warn(msg, Warning)
        return

    parser.read(path)
    update()


def update():
    if parser.has_section("opentsdb"):
        global OPENTSDB_BATCH_SIZE
        OPENTSDB_BATCH_SIZE = parser.getint("btch_size", OPENTSDB_BATCH_SIZE)

        global OPENTSDB_HOST
        OPENTSDB_HOST = parser.getint("host", OPENTSDB_HOST)

        global OPENTSDB_PORT
        OPENTSDB_PORT = parser.getint("port", OPENTSDB_PORT)

        global OPENTSDB_PROTOCOL
        OPENTSDB_PROTOCOL = parser.getint("protocol", OPENTSDB_PROTOCOL)
