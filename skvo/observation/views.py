from rest_framework.views import APIView
from rest_framework.response import Response
from utils import post
from observation import models

import logging
# Create your views here.


class Metadata(APIView):
    @staticmethod
    def validate_data(post_data):
        # todo: add validation logic here
        return post_data

    # rename fn to post
    def get(self, request):
        post_data = post.get_post_data(request)
        # validated_data = self.validate_data(post_data)
        import pickle
        import os
        post_data = pickle.load(open(os.path.join(os.path.expanduser("~/"), "post_data.pickle"), "rb"))
        post_data["instrument.field_of_view"] = post_data["instrument.field_of_view"].split(".")[-1]
        post_data["bandpass.spectral_band_type"] = "optical"
        post_data["access.access"] = "open"

        try:
            target, _ = self.get_or_create_target(post_data)
            bandpass, _ = self.get_or_create_bandpass(post_data)
            instrument, _ = self.get_or_create_instrument(post_data)
            facility, _ = self.get_or_create_facility(post_data)
            organisation, _ = self.get_or_create_organisatiion(post_data)
            access_rights, _ = self.get_or_create_access_rights(post_data)
            dataid, _ = self.get_or_create_dataid(post_data)
            observation, _ = 0, 0

        except Exception as e:
            raise
        # todo: finish metedata uploader and at the end return relvant information or raise in case off error
        # todo: add response logic here
        return Response(post_data)

    @classmethod
    def get_or_create_observation(cls, access, target, instrument, facility):
        return models.Observation.objects.get_or_create()
        return None, None

    @classmethod
    def get_or_create_dataid(cls, post_data, organisation=None):
        # todo: do the same for another methods taking instance of model or remove it from this one
        if organisation is None:
            organisation, _ = cls.get_or_create_organisatiion(post_data)

        kwargs = cls.parse_kargs(post_data, "dataid")
        return models.DataId.objects.get_or_create(dict(**kwargs, organisation_id=organisation))

    # todo: refactor methods bellow to only single method
    @classmethod
    def get_or_create_target(cls, post_data):
        kwargs = cls.parse_kargs(post_data, "target")
        return models.Target.objects.get_or_create(kwargs)

    @classmethod
    def get_or_create_bandpass(cls, post_data):
        kwargs = cls.parse_kargs(post_data, "bandpass")
        return models.Bandpass.objects.get_or_create(kwargs)

    @classmethod
    def get_or_create_instrument(cls, post_data):
        kwargs = cls.parse_kargs(post_data, "instrument")
        return models.Instrument.objects.get_or_create(kwargs)

    @classmethod
    def get_or_create_facility(cls, post_data):
        kwargs = cls.parse_kargs(post_data, "facility")
        return models.Facility.objects.get_or_create(kwargs)

    @classmethod
    def get_or_create_organisatiion(cls, post_data):
        kwargs = cls.parse_kargs(post_data, "organisation")
        return models.Organisation.objects.get_or_create(kwargs)

    @classmethod
    def get_or_create_access_rights(cls, post_data):
        kwargs = cls.parse_kargs(post_data, "access")
        return models.AccessRights.objects.get_or_create(kwargs)


    @staticmethod
    def parse_kargs(post_data, leading_kw):
        return {".".join(key.split(".")[1:]): val for key, val in post_data.items() if str(key).startswith(leading_kw)}
