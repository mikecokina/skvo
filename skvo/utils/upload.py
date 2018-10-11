import argparse
from conf import conf


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
        conf.read_and_update_config(args.config)

    conf.CONF_FILE = args.conf or conf.CONFIG_FILE
    conf.LOG_CONFIG = args.log or conf.LOG_CONFIG

    conf.OPENTSDB_HOST = args.tsdb_host or conf.OPENTSDB_HOST
    conf.OPENTSDB_PORT = args.tsdb_port or conf.OPENTSDB_PORT
    conf.OPENTSDB_PROTOCOL = args.tsdb_protocol or conf.OPENTSDB_PROTOCOL
    conf.OPENTSDB_BATCH_SIZE = args.tsdb_batch_size or conf.OPENTSDB_BATCH_SIZE

    conf.set_up_logging()

if __name__ == '__main__':
    main()
