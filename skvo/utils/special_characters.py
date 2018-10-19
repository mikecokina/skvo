import re
import codecs
from collections import Iterable
import numpy as np
import pandas as pd
from conf.config import SCHAR_REVERSE, SCHAR_PATTERN


def _to_array(obj):
    return pd.Series(obj, dtype=np.dtype('object')).values \
        if isinstance(obj, Iterable) and not isinstance(obj, str) else np.array([obj])


def _array_to_original_type(array, orig):
    # not iterable
    if not isinstance(orig, Iterable) or isinstance(orig, str):
        return array[0]
    # numpy array
    elif isinstance(orig, np.ndarray):
        return array
    # list
    elif isinstance(orig, list):
        return array.tolist()
    # series (set index)
    elif isinstance(orig, pd.Series):
        series = pd.Series(array, index=orig.index)
        return series
    else:
        return array


def multiple_replace(text, adict):
    if len(adict) == 0:
        return text
    rx = re.compile('|'.join(map(re.escape, adict)))

    def one_xlat(match):
        return adict[match.group(0)]
    return rx.sub(one_xlat, text)


def special_characters_encode(obj):
    obj_arr = _to_array(obj)
    hexify = codecs.getencoder('hex')
    new_obj = list()
    for val in obj_arr:
        rgx_output = re.finditer(SCHAR_PATTERN, val)
        rchars = {c: str(hexify(bytes(str(c).encode('utf-8')))[0].decode('utf-8')).lower()
                  for c in set([g.group(0) for g in rgx_output])}
        new_val = ''.join([char if char not in rchars.keys() else '-{}'.format(rchars.get(char)) for char in val])
        new_obj.append(new_val)
    return _array_to_original_type(np.array(new_obj), obj)


def special_characters_decode(obj):
    obj_arr = _to_array(obj)
    new_obj = list()
    for val in obj_arr:
        rgx_output = re.finditer(SCHAR_REVERSE, val)
        rchars_hex = {c: codecs.decode(c.replace('-', ''), "hex").decode('utf-8')
                      for c in set([g.group(0) for g in rgx_output])}
        new_obj.append(multiple_replace(val, rchars_hex))
    return _array_to_original_type(np.array(new_obj), obj)
