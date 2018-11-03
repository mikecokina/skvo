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


def sha512_content(content):
    sha512 = hashlib.sha512()
    sha512.update(content)
    sha512_hash = sha512.hexdigest()
    return sha512_hash


def sha256_content(content):
    sha256 = hashlib.sha256()
    sha256.update(content)
    sha256_hash = sha256.hexdigest()
    return sha256_hash
