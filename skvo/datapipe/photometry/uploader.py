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


class PhotometryProcessor(object):
    def __init__(self):
        pass


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


def run():
    config.set_up_logging()
    logger = logging.getLogger('photometry-uploader')
    logger.info("running photometry uploader")

    sources = fs.get_sources(config.BASE_PATH)
    data_locations = fs.get_data_locations(config.BASE_PATH, sources)

    metadata_importer = MetadataHttpImporter(server="http://localhost:8082")
    tsdb_importer = OpenTsdbHttpImporter(server=config.OPENTSDB_SERVER, batch_size=config.OPENTSDB_BATCH_SIZE)
    media_importer = MediaHttpImporter(server="http://localhost:8082")

    for source, dtables_paths in data_locations.items():
        for dtables_path in dtables_paths:
            full_dtables_path = fs.normalize_path(os.path.join(config.BASE_PATH, dtables_path))
            bandpass_fs_uid = fs.parse_bandpass_uid_from_path(dtables_path)
            target_fs_uid = fs.parse_target_from_path(dtables_path)
            start_date = fs.parse_date_from_path(dtables_path)
            dtable_name = fs.get_dtable_name_from_path(full_dtables_path)
            metatable_name = fs.get_metatable_name_from_path(full_dtables_path)
            full_media_path = fs.get_corresponding_media_path(full_dtables_path)

            logger.debug("reading metadata and data for object: {}, datetime: {}, bandpass: {}, source: {}"
                         "".format(target_fs_uid, datetime.date.strftime(start_date, "%Y-%m-%d"),
                                   bandpass_fs_uid, source))

            metadata = read.read_csv_file(os.path.join(full_dtables_path, metatable_name))
            metadata = transform.convert_df_float_values(metadata)
            metadata = transform.convert_df_int_values(metadata)

            data = read.read_csv_file(os.path.join(full_dtables_path, dtable_name))
            data = transform.convert_df_float_values(data)
            data = transform.convert_df_int_values(data)

            joined_df = transform.join_photometry_data(data, metadata)

            metadata_json = transform.photometry_data_to_metadata_json(metadata, data, source)
            # metadata_import_response = metadata_importer.imp(metadata_json)
            # observation_uuid = transform.get_response_observation_uuid(metadata_import_response)
            # observation_id = transform.get_response_observation_id(metadata_import_response)

            observation_id = 5
            # tsdb_observation_id_metrics = transform.observation_id_data_df_to_tsdb_metrics(joined_df, source,
            #                                                                                observation_id)
            # tsdb_timeseries_metrics = transform.df_to_timeseries_tsdb_metrics(joined_df, source)
            # tsdb_exposure_metrics = transform.df_to_exposure_tsdb_metrics(joined_df, source)
            # tsdb_errors_metrics = transform.df_to_errors_tsdb_metrics(joined_df, source)
            #
            # lambdas = [
            #     lambda: tsdb_importer.imp(tsdb_observation_id_metrics),
            #     lambda: tsdb_importer.imp(tsdb_timeseries_metrics),
            #     lambda: tsdb_importer.imp(tsdb_errors_metrics),
            #     lambda: tsdb_importer.imp(tsdb_exposure_metrics)
            # ]
            # async_import(lambdas)

            media_files = fs.get_media_list_on_path(full_media_path)

            for mf in media_files:
                full_media_file_path = os.path.join(full_media_path, mf)
                # get raw content of image
                media_file_content = fs.read_file_as_binary(full_media_file_path)
                # gzip content
                media_file_gzip = utils.compress(media_file_content)
                # computet md5 crc
                crc = utils.md5_raw_content(media_file_gzip)
                # prepare avro chema compatible data
                avro_schema_data = \
                    transform.avro_msg_serializer(media_file_gzip, mf, metadata, data, source, crc)
                # prepare avro binary
                avro_raw_data = transform.encode_avro_message(avro_schema_data)

                # import
                media_importer.imp(avro_raw_data, avro_schema_data["filename"])

            # photometry_loader = transform.get_photometry_loader(transform=None, init_sink=None)


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
