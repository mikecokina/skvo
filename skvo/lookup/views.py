import logging

from astropy.coordinates import SkyCoord as skycoord
from django.db.models import Q
from django.http import HttpResponseBadRequest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from datapipe.photometry import config
from datapipe.photometry import read_tsdb
from datapipe.photometry import transform
from observation.models import Photometry
from skvo.settings import TSDB_CONNECTOR
from utils import post
from utils import utils

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
            dataset=data.get("dataset", None),
            target=data.get("target", None),
            ra=data.get("ra", None),
            de=data.get("de", None),
            box_size_ra=data.get("box_size_ra", DEFAULT_BOX_SIZE_RA),
            box_size_de=data.get("box_size_de", DEFAULT_BOX_SIZE_DE)
        )

        if not kwargs["target"] and (not kwargs["ra"] and not kwargs["de"]):
            raise Exception("missing argument `target` or arguments `ra` & `de` in request")

    except Exception as e:
        msg = "Bad Request. {}".format(str(e))
        logging.exception(msg)
        raise KeyError(msg)
    return kwargs


def prepare_photometry_model_filter_clause(validated_data):
    filters = dict()

    size_ra_bottom = utils.normalize_ra(validated_data["ra"] - validated_data["box_size_ra"])
    size_ra_top = utils.normalize_ra(validated_data["ra"] + validated_data["box_size_ra"])

    size_de_bottom = validated_data["de"] - validated_data["box_size_de"]
    size_de_top = validated_data["de"] + validated_data["box_size_de"]

    if validated_data["box_size_ra"] >= 360 / 2.0:
        size_ra_bottom, size_ra_top = 0, 360

    if size_ra_bottom > size_ra_top:
        filters.update(
            dict(
                query_like=
                lambda: Q(observation__target__right_ascension__gte=size_ra_bottom) |
                Q(observation__target__right_ascension__gte=size_ra_bottom) &
                Q(observation__target__right_ascension__gte=0)
            )
        )
    else:
        filters.update(**dict(
            observation__target__right_ascension__gte=size_ra_bottom,
            observation__target__right_ascension__lte=size_ra_top
        ))
    filters.update(**dict(observation__target__declination__range=(size_de_bottom, size_de_top)))
    return filters


def get_photometry_observation(validated_data):
    filters = prepare_photometry_model_filter_clause(validated_data)
    observations = Photometry.objects.filter(**filters) \
        if "query_like" not in filters else Photometry.objects.filter(filters.pop("query_like")(), **filters)
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


def get_targets_coordinates(validated_data):
    if validated_data["ra"] and validated_data["de"]:
        return utils.normalize_ra(float(validated_data["ra"])), float(validated_data["de"])
    elif validated_data["target"]:
        coord = skycoord.from_name(str(validated_data["target"]))
        return float(coord.ra.deg), float(coord.dec.deg)


class LookupPostView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = post.get_post_data(request)
            validated_data = _parse_lookup_request(data)
        except (KeyError, ValueError, LookupError) as e:
            return HttpResponseBadRequest(content=str(e))

        validated_data["ra"], validated_data["de"] = get_targets_coordinates(validated_data)
        observations = get_photometry_observation(validated_data)
        metadata = get_observation_intervals(observations)
        samples = read_tsdb.get_samples(tsdb_connector=TSDB_CONNECTOR, metadata=metadata, version=config.NUM_VERSION)
        samples = transform.add_separation_to_samples_dict(samples)
        return Response(samples, status=status.HTTP_200_OK)


class LookupGetView(APIView):
    def get(self, request, **kwargs):
        return Response("GET_OK", status=status.HTTP_200_OK)
