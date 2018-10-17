import argparse
import logging
import os

from conf import config
from datapipe.photometry import filesystem as fs
from datapipe.photometry import transform


class PhotometryProcessor(object):
    def __init__(self):
        pass


def run():
    config.set_up_logging()
    logger = logging.getLogger('photometry-uploader')
    logger.info("running photometry uploader")

    sources = fs.get_sources(config.BASE_PATH)
    data_locations = fs.get_data_locations(config.BASE_PATH, sources)

    for source, dtables_paths in data_locations.items():
        for dtables_path in dtables_paths:
            full_dtables_path = fs.normalize_path(os.path.join(config.BASE_PATH, dtables_path))
            bandpass_fs_uid = fs.parse_bandpass_uid_from_path(dtables_path)
            target_fs_uid = fs.parse_target_from_path(dtables_path)
            start_date = fs.parse_date_from_path(dtables_path)
            dtable_name = fs.get_dtable_name_from_path(full_dtables_path)
            metatable_name = fs.get_metatable_name_from_path(full_dtables_path)






    # importer = None
    # photometry_loader = transform.get_photometry_loader(transform=None, init_sink=None)


def main():
    parser = argparse.ArgumentParser(description="")

    parser.add_argument('--config', nargs='?', help='path to configuration file')
    parser.add_argument('--log', nargs='?', help='path to json logging configuration file')

    parser.add_argument('--tsdb-host', nargs='?', help='TSD host name.')
    parser.add_argument('--tsdb-port', nargs='?', help='TSD port number.')
    parser.add_argument('--tsdb-protocol', nargs='?', help='TSD protocol.')
    parser.add_argument('--tsdb-batch-size', nargs='?', type=int, help='maximum batch size for OpenTSDB http input')

    parser.add_argument('--base-path', nargs='?', type=str, help='base path to data storage')

    args = parser.parse_args()

    if args.config:
        config.read_and_update_config(args.config)

    config.CONFIG_FILE = args.config or config.CONFIG_FILE
    config.LOG_CONFIG = args.log or config.LOG_CONFIG

    config.OPENTSDB_HOST = args.tsdb_host or config.OPENTSDB_HOST
    config.OPENTSDB_PORT = args.tsdb_port or config.OPENTSDB_PORT
    config.OPENTSDB_PROTOCOL = args.tsdb_protocol or config.OPENTSDB_PROTOCOL
    config.OPENTSDB_BATCH_SIZE = args.tsdb_batch_size or config.OPENTSDB_BATCH_SIZE

    config.BASE_PATH = args.base_path or config.BASE_PATH
    config.set_up_logging()

    run()

if __name__ == '__main__':
    main()
