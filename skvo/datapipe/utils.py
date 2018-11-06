from utils import special_characters


def parse_bandpass_from_metric(metric):
    return special_characters.special_characters_decode(metric.split(".")[1])
