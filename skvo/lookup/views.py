import logging

from astropy.coordinates import SkyCoord as skycoord
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from conf import config as gconf
from datapipe.photometry import config as pconf
from datapipe.photometry import read_tsdb
from datapipe.photometry import transform
from observation import models
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
            ra=float(data.get("ra")) if data.get("ra") else None,
            de=float(data.get("de")) if data.get("ra") else None,
            box_size_ra=float(data.get("box_size_ra")) if data.get("box_size_ra") else DEFAULT_BOX_SIZE_RA,
            box_size_de=float(data.get("box_size_de")) if data.get("box_size_de") else DEFAULT_BOX_SIZE_DE
        )

        if kwargs["target"] is None and (kwargs["ra"] is None and kwargs["de"] is None):
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
                lambda: (Q(observation__target__right_ascension__gte=size_ra_bottom) |
                Q(observation__target__right_ascension__lte=size_ra_top)) &
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
            "instrument_hash": o.observation.instrument.instrument_hash,
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


def get_samples(validated_data):
    observations = get_photometry_observation(validated_data)
    if observations:
        metadata = get_observation_intervals(observations)
        samples = read_tsdb.get_samples(tsdb_connector=TSDB_CONNECTOR, metadata=metadata, version=pconf.VERSION)
        samples = transform.add_separation_to_samples_dict(samples)
        return samples
    return dict()


class PhotometryLookupPostView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = post.get_post_data(request)
            validated_data = _parse_lookup_request(data)
        except (KeyError, ValueError, LookupError) as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        validated_data["ra"], validated_data["de"] = get_targets_coordinates(validated_data)
        samples = get_samples(validated_data)
        return Response(samples, status=status.HTTP_200_OK)


class PhotometryLookupGetView(APIView):
    def get(self, request, *args, **kwargs):
        acceptable_params = ["dataset", "target", "ra", "de", "box_size_ra", "box_size_de"]
        try:
            data = {ap: kwargs.get(ap, None) for ap in acceptable_params}
            validated_data = _parse_lookup_request(data)
        except (KeyError, ValueError, LookupError) as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        validated_data["ra"], validated_data["de"] = get_targets_coordinates(validated_data)
        samples = get_samples(validated_data)
        return Response(samples, status=status.HTTP_200_OK)


class PhotometryARef(APIView):
    def get(self, request, *args, **kwargs):
        import datetime

        validated_data = {
            "start_date": datetime.datetime.strptime("2017-12-04 00:00:01", "%Y-%m-%d %H:%M:%S"),
            "end_date": datetime.datetime.strptime("2017-12-04 00:00:15", "%Y-%m-%d %H:%M:%S"),
            "observation": {
                "id": 1
            },
            "instrument": {
                "instrument_hash": "f104c9851b3d5efc373eafd49db9ffca"
            },
            "target": {
                "id": 1,
                "catalogue_value": "bet_Lyr"
            },
            "bandpass": {
                "bandpass_uid": "johnson.u",
            },
            "dataid": {
                "source": "upjs"
            }
        }

        observation_model = models.get_observation_by_id(uid=validated_data["observation"]["id"])
        access = str(observation_model.access.access).lower()
        sdate, edate = models.get_photometry_timerange_by_observation_id(validated_data["observation"]["id"])

        # after debug, move this to validation
        validated_data["start_date"] = gconf.UTC_TIMEZONE.localize(validated_data["start_date"])
        validated_data["end_date"] = gconf.UTC_TIMEZONE.localize(validated_data["end_date"])

        # in case, user is requesting bigger timerange, cut it out
        validated_data["start_date"] = sdate if validated_data["start_date"] < sdate else validated_data["start_date"]
        validated_data["end_date"] = edate if validated_data["end_date"] > edate else validated_data["end_date"]

        if access in ["open"]:
            data = read_tsdb.get_data(TSDB_CONNECTOR,
                                      target=str(validated_data["target"]["catalogue_value"]),
                                      instrument_hash=str(validated_data["instrument"]["instrument_hash"]),
                                      bandpass_uid=str(validated_data["bandpass"]["bandpass_uid"]),
                                      source=str(validated_data["dataid"]["source"]),
                                      observation_id=int(validated_data["observation"]["id"]),
                                      start_date=validated_data["start_date"],
                                      end_date=validated_data["end_date"],
                                      version=pconf.VERSION)
            return Response(data)
        return Response("We don't do that here")






