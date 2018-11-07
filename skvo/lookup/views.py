import logging

from rest_framework.response import Response
from rest_framework.views import APIView

from observation.models import Photometry
from skvo.settings import TSDB_CONNECTOR
from datapipe.photometry import read_tsdb
from datapipe.photometry import config



# Create your views here.

DEFAULT_BOX_SIZE_RA, DEFAULT_BOX_SIZE_DE = 5, 5


def _parse_lookup_request(data):
    """
    parse data from lookup/searching request

    :param data: dict
    :return: dict
    """
    try:
        kwargs = dict(
            dataset=data["dataset"],
            target=data.get("target", None),
            ra=data.get("ra", None),
            de=data.get("de", None),
            box_size_ra=data.get("box_size_ra", DEFAULT_BOX_SIZE_RA),
            box_size_de=data.get("box_size_de", DEFAULT_BOX_SIZE_DE)
        )
    except Exception as e:
        msg = "Bad Request. {}".format(str(e))
        logging.exception(msg)
        raise KeyError(msg)
    return kwargs


def get_photometry_observation():
    observations = Photometry.objects.filter()
    return observations


def get_observation_intervals(observations):
    return [
        {
            "start_date": o.start_date,
            "end_date": o.end_date,
            "observation_id": o.observation_id,
            "instrument_uuid": o.observation.instrument.instrument_uuid,
            "source": o.observation.dataid.source,
            "target": o.observation.target.catalogue_value,
            "bandpass": o.bandpass.bandpass_uid
        }
        for o in observations
    ]


class LookupPostView(APIView):
    def post(self, request, *args, **kwargs):
        return Response("POST_OK", status=200)

    def get(self, request, *args, **kwargs):
        observations = get_photometry_observation()
        metadata = get_observation_intervals(observations)
        samples = read_tsdb.get_samples(tsdb_connector=TSDB_CONNECTOR, metadata=metadata, version=config.NUM_VERSION)
        return Response(samples, status=200)


class LookupGetView(APIView):
    def get(self, request, **kwargs):
        return Response("GET_OK", status=200)
