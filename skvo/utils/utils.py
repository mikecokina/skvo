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


def normalize_ra(ra):
    sign = 1 if ra >= 0 else -1
    ra = (abs(ra) % 360) * sign
    return ra if ra >= 0 else ra + 360.0


def find_key(keys, contain):
    _key = [key for key in keys if contain in key]
    if len(_key) > 1:
        raise ValueError("there is more than one key, that contain value `{}`".format(contain))
    return _key[0]
