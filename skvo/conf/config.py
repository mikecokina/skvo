from configparser import ConfigParser
from logging import config as logconf

import os
import json
import logging
import warnings
import pytz


parser = ConfigParser()
venv_config = os.path.join(os.environ.get('VIRTUAL_ENV', ''), 'conf', 'skvo.ini')

if not os.path.isfile(venv_config):
    raise LookupError("Couldn't resolve configuration file. To define it \n "
                      "  - add conf/skvo.ini under your virtualenv root\n")
CONFIG_FILE = venv_config
LOG_CONFIG = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'conf', 'skvo-log.json')

BASE_PATH = os.path.expanduser("~/data")
EXPORT_PATH = os.path.expanduser("~/export_data")

OPENTSDB_SERVER = "http://localhost:4242"
OPENTSDB_BATCH_SIZE = 10000

parser.read(CONFIG_FILE)


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
        OPENTSDB_BATCH_SIZE = parser.getint("opentsdb", "batch_size", fallback=OPENTSDB_BATCH_SIZE)

        global OPENTSDB_SERVER
        OPENTSDB_SERVER = parser.get("opentsdb", "server", fallback=OPENTSDB_SERVER)

    if parser.has_section("general"):
        global BASE_PATH
        BASE_PATH = parser.get("general", "base_path", fallback=BASE_PATH)

        global EXPORT_PATH
        EXPORT_PATH = parser.get("general", "export_path", fallback=EXPORT_PATH)


DTYPES_BASE_DIR = {
    "photometry": "photometry",
    "spectroscopy": "spectroscopy"
}

SCHAR_PATTERN = r'[^a-zA-Z0-9_]'
SCHAR_REVERSE = r'(\-){1}([a-z0-9]){2}'


TIMESTAMP_PARSING_COLUMNS = ["ts.timestamp"]

PHOTOMETRY_FLOAT_FIELDS = ["ts.magnitude", "target.right_ascension", "target.declination", "instrument.field_of_view"]
PHOTOMETRY_INT_FIELDS = ["ts.flux_calibration_level", "ts.exposure"]

OPENTSDB_QUERY = dict(
    ms=True,
    show_tsuids=False,
    no_annotations=False,
    global_annotations=False,
    show_summary=False,
    show_stats=False,
    show_query=False,
    delete=False,
    timezone='UTC',
    use_calendar=False,
)

UTC_TIMEZONE = pytz.timezone("UTC")

update()
