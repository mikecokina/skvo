import re
import datetime
import subprocess
import logging
import argparse
from threading import Thread

from conf import config
from pyopentsdb import tsdb
from abc import ABCMeta
from abc import abstractmethod
from queue import Queue


class Eraser(metaclass=ABCMeta):
    def __init__(self, tsdb_bin, n_threads=10, chunk_size=5):
        self._tsdb_connection = get_tsdb_connetion()
        self._tsdb_bin = tsdb_bin
        self._n_threads = n_threads
        self._chunk_size = chunk_size
        self._logger = logging.getLogger(str(self))
        
    def __str__(self):
        return str(Eraser.__name__)

    def erase(self, star_date, end_date, metrics=None, regex=None, erase_metrics=False):
        __WORKER_RUN__ = True

        def erase_worker():
            while __WORKER_RUN__:
                _metrics_to_erase = metrics_erase_queue.get()
                if _metrics_to_erase == "TERMINATOR":
                    break

                if not error_queue.empty():
                    break

                try:
                    self.erase_data(star_date, end_date, _metrics_to_erase)
                    if erase_metrics:
                        self.erase_metrics(_metrics_to_erase)
                except Exception as we:
                    error_queue.put(we)
                    break

        suggest_q = None
        if regex is not None:
            metrics = None
            suggest_q, regex = self.tsdb_suggest_query_parser(regex), self.regex_parser(regex)

        try:
            pass
            metrics_to_erase = self.metrics_to_erase(metrics, regex, suggest_q)
            metrics_erase_queue = Queue()
            error_queue = Queue()
            threads = list()

            for i in range(0, len(metrics_to_erase), self._chunk_size):
                metrics_erase_queue.put(metrics_to_erase[i:i + self._chunk_size])

            for _ in range(self._n_threads):
                metrics_erase_queue.put("TERMINATOR")

            for _ in range(self._n_threads):
                t = Thread(target=erase_worker)
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

    @abstractmethod
    def erase_data(self, *args, **kwargs):
        pass

    def erase_metrics(self, metrics):
        for metric in metrics:
            self._logger.info("Delete metric {}".format(metric))
            command = [self._tsdb_bin, 'uid', 'delete', 'metric', metric]
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL)
            try:
                _, _ = process.communicate(timeout=360)
            except subprocess.TimeoutExpired:
                self._logger.error("Expired time allowed to delete metric {}".format(metric))
                raise
        self.dropcaches()

    def metrics_to_erase(self, metrics, regex, suggest_q):
        return metrics if metrics is not None else self._tsdb_connection.metrics(q=suggest_q, max=100000, regexp=regex)

    @staticmethod
    def prepare_queries(metrics):
        return [{"aggregator": "none", "metric": metric} for metric in metrics]

    @staticmethod
    def tsdb_suggest_query_parser(expression):
        # if not * in regex, entire expression is taken as query pattern for tsdb api suggest
        if "*" not in expression:
            return expression
        try:
            # try to find out leading expression to be used as query for tsdb api suggest
            m = re.search(r"^([A-Za-z0-9._]+)\*.*$", expression)
            return m.group(1)
        except AttributeError:
            # if no match was found, expression probably tarts with * or other not allowed symbol
            raise Exception("Not allowed regular expression")

    @staticmethod
    def regex_parser(regex):
        regex = regex.replace(".", "\.")
        regex = regex.replace("*", ".*")
        regex = "^{}$".format(regex)
        return regex

    def dropcaches(self):
        self._tsdb_connection.dropcaches()


class TsdbEraser(Eraser):
    def __init__(self, **kwargs):
        super(TsdbEraser, self).__init__(**kwargs)

    def __str__(self):
        return str(TsdbEraser.__name__)

    def erase_data(self, start_date, end_date, metrics):
        start_date = datetime.datetime(start_date.year, start_date.month, start_date.day, start_date.hour, 0, 0)
        end_date = datetime.datetime(end_date.year, end_date.month, end_date.day, end_date.hour, 0, 0)
        start_date = start_date.strftime("%Y/%m/%d-%H:%M:%S")
        end_date = end_date.strftime("%Y/%m/%d-%H:%M:%S")

        for metric in metrics:
            self._logger.info("Delete metric data {}".format(metric))
            command = [self._tsdb_bin, 'scan', start_date, end_date, "none", metric, "--delete"]
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL)
            try:
                _, _ = process.communicate(timeout=360)
            except subprocess.TimeoutExpired:
                self._logger.error("Expired time allowed to delete data for metric {}".format(metric))
                raise


class HttpEraser(Eraser):
    def __init__(self, **kwargs):
        super(HttpEraser, self).__init__(**kwargs)

    def __str__(self):
        return str(HttpEraser.__name__)

    @staticmethod
    def prepare_queries(metrics):
        return [{"aggregator": "none", "metric": metric} for metric in metrics]

    def erase_data(self, start_date, end_date, metrics):
        for metric in metrics:
            self._logger.info("Delete metric data {}".format(metric))
        queries_to_erase = self.prepare_queries(metrics)
        self._tsdb_connection.query(start=start_date, end=end_date, ms=True,
                                    metrics=queries_to_erase, delete=True)


def get_tsdb_connetion():
    return tsdb.tsdb_connection(host=config.TSDB_SERVER)


def main(start_date, end_date, metrics=None, regex=None, eraser=None, erase_metrics=False,
         tsdb_bin='/usr/share/opentsdb/bin/tsdb', chunk_size=10, n_threads=10):
    if eraser == "http":
        eraser_o = HttpEraser(tsdb_bin=tsdb_bin, chunk_size=chunk_size, n_threads=n_threads)
    elif eraser == "tsdb":
        eraser_o = TsdbEraser(tsdb_bin=tsdb_bin, chunk_size=chunk_size, n_threads=n_threads)
    else:
        raise Exception("Invalid eraser class")

    eraser_o.erase(star_date=start_date, end_date=end_date, regex=regex, metrics=metrics, erase_metrics=erase_metrics)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="")

    parser.add_argument('--log', nargs='?', help='path to logging json configuration file')

    parser.add_argument('--tsdb-server', nargs='?', type=str, help='TSD host name.')

    parser.add_argument('--n-threads', nargs='?', type=int, help='number of threads deleting data')
    parser.add_argument('--chunk-size', nargs='?', type=int, help='number of metrics prepared for deletion at once')

    parser.add_argument('--start-date', nargs='?', type=str, help='"%Y/%m/%d-%H:%M:%S"')
    parser.add_argument('--end-date', nargs='?', type=str, help='"%Y/%m/%d-%H:%M:%S"')
    parser.add_argument('--regex', nargs='?', type=str, help='e.g. 1b023.*.v0')
    parser.add_argument('--metrics', nargs='?', type=str, help='e.g. sys.cpu.v0,sys.cpu.v1,sys.cpu.v2')
    parser.add_argument('--eraser', nargs='?', type=str, help='tsdb/http')
    parser.add_argument('--tsdb-bin', nargs='?', type=str, help='path to tsdb bin')

    parser.add_argument('--erase-metrics', action='store_true', help='if provided, erase also metrics')

    argsp = parser.parse_args()

    config.TSDB_SERVER = argsp.tsdb_server or config.OPENTSDB_SERVER
    config.LOG_CONFIG = argsp.log or config.LOG_CONFIG

    # set up logging
    config.set_up_logging()

    d_start_date = datetime.datetime.strptime(argsp.start_date, "%Y/%m/%d-%H:%M:%S")
    d_end_date = datetime.datetime.strptime(argsp.end_date, "%Y/%m/%d-%H:%M:%S")
    d_regex = argsp.regex or None
    d_metrics = argsp.metrics.split(",") if argsp.metrics is not None else None
    d_eraser = argsp.eraser or None
    d_erase_metrics = argsp.erase_metrics or False
    d_tsdb_bin = argsp.tsdb_bin or '/usr/share/opentsdb/bin/tsdb'
    d_chunk_size = argsp.chunk_size or 10
    d_n_threads = argsp.n_threads or 10

    if d_regex is None and d_metrics is None:
        raise Exception("regex or metrics to delete has to be specified")

    main(start_date=d_start_date, end_date=d_end_date, metrics=d_metrics, regex=d_regex, eraser=d_eraser,
         erase_metrics=d_erase_metrics, tsdb_bin=d_tsdb_bin, chunk_size=d_chunk_size, n_threads=d_n_threads)
