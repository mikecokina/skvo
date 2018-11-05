import argparse
import datetime
import logging
import os
from queue import Queue
from threading import Thread

from utils import utils
from conf import config
from datapipe.importers import MetadataHttpImporter, OpenTsdbHttpImporter, MediaHttpImporter
from datapipe.photometry import filesystem as fs
from datapipe.photometry import read
from datapipe.photometry import transform


def async_import(lambda_fns):
    __WORKER_RUN__ = True

    def async_importer_worker():
        while __WORKER_RUN__:
            lamda_fn = lamda_fns_queue.get()
            if lamda_fn == "TERMINATOR":
                break
            if not error_queue.empty():
                break
            try:
                lamda_fn()
            except Exception as we:
                error_queue.put(we)
                break
            lamda_fn()

    n_threads = 4
    lamda_fns_queue = Queue()
    error_queue = Queue()
    threads = list()

    try:
        for lambda_fn in lambda_fns:
            lamda_fns_queue.put(lambda_fn)

        for _ in range(n_threads):
            lamda_fns_queue.put("TERMINATOR")

        for _ in range(n_threads):
            t = Thread(target=async_importer_worker())
            threads.append(t)
            t.daemon = True
            t.start()

        for t in threads:
            t.join()
    except KeyboardInterrupt:
        raise
    finally:
        __WORKER_RUN__ = False

    if not error_queue.empty():
        raise error_queue.get()


class MetadataProcessor(object):
    def __init__(self, server=None):
        self._importer = MetadataHttpImporter(server=server or "http://localhost:8082")
        self._logger = logging.getLogger(MetadataProcessor.__name__)

    @staticmethod
    def get_metadata(path, filename):
        metadata = read.read_csv_file(os.path.join(path, filename))
        metadata = transform.convert_df_float_values(metadata)
        metadata = transform.convert_df_int_values(metadata)
        return metadata

    def process(self, metadata, data, source):
        self._logger.info("Starting metada processor")
        metadata_json = transform.photometry_data_to_metadata_json(metadata, data, source)
        metadata_import_response = self._importer.imp(metadata_json)
        observation_id = transform.get_response_observation_id(metadata_import_response)
        instrument_uuid = transform.get_response_instrument_uuid(metadata_import_response)

        self._logger.info("Exiting metadata processor")
        return observation_id, instrument_uuid


class DataProcessor(object):
    def __init__(self):
        self._importer = OpenTsdbHttpImporter(server=config.OPENTSDB_SERVER, batch_size=config.OPENTSDB_BATCH_SIZE)
        self._logger = logging.getLogger(DataProcessor.__name__)

    @staticmethod
    def get_data(path, filename):
        data = read.read_csv_file(os.path.join(path, filename))
        data = transform.convert_df_float_values(data)
        data = transform.convert_df_int_values(data)
        return data

    def process(self, metadata, data, source, observation_id):
        self._logger.info("Starting data processor")
        joined_df = transform.join_photometry_data(data, metadata)
        tsdb_oid_metrics = transform.observation_id_data_df_to_tsdb_metrics(joined_df, source, observation_id)
        tsdb_timeseries_metrics = transform.df_to_timeseries_tsdb_metrics(joined_df, source)
        tsdb_exposure_metrics = transform.df_to_exposure_tsdb_metrics(joined_df, source)
        tsdb_errors_metrics = transform.df_to_errors_tsdb_metrics(joined_df, source)

        lambdas = [
            lambda: self._importer.imp(tsdb_oid_metrics),
            lambda: self._importer.imp(tsdb_timeseries_metrics),
            lambda: self._importer.imp(tsdb_errors_metrics),
            lambda: self._importer.imp(tsdb_exposure_metrics)
        ]
        self._logger.info("Starting async metrics push")
        async_import(lambdas)
        self._logger.info("Finishing async metrics push")
        self._logger.info("Exiting data processor")


class MediaProessor(object):
    def __init__(self, server=None):
        self._importer = MediaHttpImporter(server=server or "http://localhost:8082")
        self._logger = logging.getLogger(MediaProessor.__name__)

    def process(self, path, metadata, data, source):
        self._logger.info("Exiting media processor")
        media_files = fs.get_media_list_on_path(path)
        media_files = fs.sort_files_by_part(media_files)

        for mf in media_files:
            full_media_file_path = os.path.join(path, mf)
            # get raw content of image
            media_file_content = fs.read_file_as_binary(full_media_file_path)
            # computet md5 crc
            crc = utils.md5_raw_content(media_file_content)
            # gzip content
            media_file_gzip = utils.compress(media_file_content)
            # prepare avro chema compatible data
            avro_schema_data = \
                transform.avro_msg_serializer(media_file_gzip, mf, metadata, data, source, crc)
            # prepare avro binary
            avro_raw_data = transform.encode_avro_message(avro_schema_data)
            # import
            self._importer.imp(avro_raw_data, avro_schema_data["filename"])
        self._logger.info("Exiting media processor")


class PhotometryProcessor(object):
    def __init__(self):
        self._metadata_proessor = MetadataProcessor()
        self._data_processor = DataProcessor()
        self._media_processor = MediaProessor()
        self._logger = logging.getLogger(PhotometryProcessor.__name__)
        self._sources = fs.get_sources(config.BASE_PATH)
        self._data_locations = fs.get_data_locations(config.BASE_PATH, self._sources)

    def process(self):
        for source, dtables_paths in self._data_locations.items():
            self._logger.info("Processing source: {}".format(source))
            for dtables_path in dtables_paths:
                full_dtables_path = fs.normalize_path(os.path.join(config.BASE_PATH, dtables_path))
                bandpass_fs_uid = fs.parse_bandpass_uid_from_path(dtables_path)
                target_fs_uid = fs.parse_target_from_path(dtables_path)
                full_media_path = fs.get_corresponding_media_path(full_dtables_path)
                dtable_name = fs.get_dtable_name_from_path(full_dtables_path)
                metatable_name = fs.get_metatable_name_from_path(full_dtables_path)
                start_date = fs.parse_date_from_path(dtables_path)

                self._logger.debug(
                    "reading metadata and data for object: {}, datetime: {}, bandpass: {}, source: {}"
                    "".format(target_fs_uid, datetime.date.strftime(start_date, "%Y-%m-%d"), bandpass_fs_uid, source))

                metadata = self._metadata_proessor.get_metadata(full_dtables_path, metatable_name)
                data = self._data_processor.get_data(full_dtables_path, dtable_name)
                oid, iuuid = self._metadata_proessor.process(metadata, data, source)
                metadata = transform.expand_metadata_with_instrument_uuid(metadata, iuuid)
                self._data_processor.process(metadata, data, source, oid)
                self._media_processor.process(full_media_path, metadata, data, source)


def run():
    config.set_up_logging()
    logger = logging.getLogger('photometry-uploader')
    logger.info("running photometry uploader")
    processor = PhotometryProcessor()
    processor.process()
    logger.info("terminating photometry uploader")


def main():
    parser = argparse.ArgumentParser(description="")

    parser.add_argument('--config', nargs='?', help='path to configuration file')
    parser.add_argument('--log', nargs='?', help='path to json logging configuration file')

    parser.add_argument('--tsdb-server', nargs='?', help='TSD host name.')
    parser.add_argument('--tsdb-batch-size', nargs='?', type=int, help='maximum batch size for OpenTSDB http input')

    parser.add_argument('--base-path', nargs='?', type=str, help='base path to data storage')

    args = parser.parse_args()

    if args.config:
        config.read_and_update_config(args.config)

    config.CONFIG_FILE = args.config or config.CONFIG_FILE
    config.LOG_CONFIG = args.log or config.LOG_CONFIG

    config.OPENTSDB_SERVER = args.tsdb_server or config.OPENTSDB_SERVER
    config.OPENTSDB_BATCH_SIZE = args.tsdb_batch_size or config.OPENTSDB_BATCH_SIZE

    config.BASE_PATH = args.base_path or config.BASE_PATH
    config.set_up_logging()

    run()


if __name__ == '__main__':
    main()
