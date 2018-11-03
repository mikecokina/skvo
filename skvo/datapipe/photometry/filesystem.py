import os
import datetime
import re

from conf import config


def get_base_path(base_path):
    return base_path if base_path is not None else config.BASE_PATH


def get_sources(base_path=None):
    """
    get source folders from base_path

    :param base_path:
    :return:
    """
    base_path = get_base_path(base_path)
    return [name for name in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, name))]


def get_data_locations(base_path=None, source=None):
    """
    get dict of all available data for give source in base_path

    :param base_path:
    :param source:
    :return:
    """
    if isinstance(source, str):
        source = [source]

    data_tree = {_source: list() for _source in source}

    for _source in source:
        tree = os.walk(os.path.join(base_path, _source, config.DTYPES_BASE_DIR["photometry"]))
        for path, dirs, _ in tree:
            if len(dirs) == 0 and "media" not in path:
                data_tree[_source].append(path)
    return data_tree


def get_targets(base_path=None):
    base_path = get_base_path(base_path)


def _get_coresponding_path(path, dirname):
    path_split = path.split(os.sep)
    path_split[-4] = dirname
    return os.sep.join(path_split)


def get_corresponding_media_path(path):
    return _get_coresponding_path(path, "media")


def get_corresponding_dtables_path(path):
    return _get_coresponding_path(path, "dtables")


def parse_bandpass_uid_from_path(path):
    return path.split(os.sep)[-1]


def parse_target_from_path(path):
    return "_".join(path.split(os.sep)[-2].split("_")[:-1])


def _parse_dt_from_path(path, date_fn):
    dt = path.split(os.sep)[-2].split("_")[-1]
    rs = re.search(r"([0-9]{4})([0-9]{2})([0-9]{2})", dt)
    return date_fn(int(rs[1]), int(rs[2]), int(rs[3]))


def parse_datetime_from_path(path):
    return _parse_dt_from_path(path, datetime.datetime)


def parse_date_from_path(path):
    return _parse_dt_from_path(path, datetime.date)


def _get_dtable_from_path(path, table_type):
    target_fs_uid = parse_target_from_path(path)
    start_date = parse_date_from_path(path)
    return "{}_{}_{}.csv".format(target_fs_uid, datetime.date.strftime(start_date, "%Y%m%d"), table_type)


def get_dtable_name_from_path(path):
    return _get_dtable_from_path(path, "data")


def get_metatable_name_from_path(path):
    return _get_dtable_from_path(path, "meta")


def normalize_path(path):
    split_path = path.split(os.sep)
    split_path = [sign for sign in split_path if sign not in [os.sep]]
    return os.sep.join(split_path)


def get_media_list_on_path(path):
    return [f for f in os.listdir(path) if is_image(f)]


def read_file_as_binary(path):
    with open(path, "rb") as rbf:
        content = rbf.read()
        return content


def write_file_as_binary(path, raw_content):
    with open(path, "wb") as wbf:
        wbf.write(raw_content)


def is_image(path):
    filename, file_extension = os.path.splitext(path)
    return True if str(file_extension).lower()[1:] in ["png", "jpg", "jpeg"] else False


def get_media_path_from_metadata(target, base_path, source, bandpass, start_date):
    date_dir = "{}{}".format(start_date.year, start_date.month)
    target_date_dir = "{}_{}{}{}" \
                      "".format(target, start_date.year, start_date.month, start_date.day)
    return os.path.join(
        base_path, source, config.DTYPES_BASE_DIR["photometry"], "media", date_dir, target_date_dir,
        bandpass
    )


def create_media_path_if_needed(path):
    os.makedirs(path, exist_ok=True)
