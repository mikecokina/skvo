import gzip
import hashlib


def md5_raw_content(raw_content):
    md5 = hashlib.md5()
    md5.update(raw_content)
    md5_crc = md5.hexdigest()
    return md5_crc


def compress(content, level=7):
    return gzip.compress(content, level)


def decompress(content):
    return gzip.decompress(content)


def check_md5_crc(content, crc):
    return True if md5_raw_content(content) == crc else False
