import argparse
from conf import config


def read_file():
    pass


def get_md5():
    pass


def prepare_message():
    pass


def run():
    pass


def main():
    parser = argparse.ArgumentParser(description="")

    parser.add_argument('--config', nargs='?', help='path to configuration file')
    parser.add_argument('--log', nargs='?', help='path to json logging configuration file')

    parser.add_argument('--tsdb-host', nargs='?', help='TSD host name.')
    parser.add_argument('--tsdb-port', nargs='?', help='TSD port number.')
    parser.add_argument('--tsdb-protocol', nargs='?', help='TSD protocol.')
    parser.add_argument('--tsdb-batch-size', nargs='?', type=int, help='maximum batch size for OpenTSDB http input')

    args = parser.parse_args()

    if args.config:
        config.read_and_update_config(args.config)

    config.CONFIG_FILE = args.config or config.CONFIG_FILE
    config.LOG_CONFIG = args.log or config.LOG_CONFIG

    config.OPENTSDB_HOST = args.tsdb_host or config.OPENTSDB_HOST
    config.OPENTSDB_PORT = args.tsdb_port or config.OPENTSDB_PORT
    config.OPENTSDB_PROTOCOL = args.tsdb_protocol or config.OPENTSDB_PROTOCOL
    config.OPENTSDB_BATCH_SIZE = args.tsdb_batch_size or config.OPENTSDB_BATCH_SIZE

    config.set_up_logging()

    run()

if __name__ == '__main__':
    main()
