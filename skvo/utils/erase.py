from utils import tsdb_eraser

from datetime import datetime
from conf import config as gconf
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s : [%(levelname)s] : %(name)s : %(message)s')

gconf.OPENTSDB_SERVER = "http://192.168.56.102:4242"

start_date = datetime(2010, 1, 1)
end_date = datetime.now()

eraser_instance = tsdb_eraser.HttpEraser(tsdb_bin="tsdb", chunk_size=10, n_threads=5)
# eraser_instance.erase(star_date=start_date, end_date=end_date, regex=regex, erase_metrics=True)
