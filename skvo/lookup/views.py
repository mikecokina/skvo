from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

import logging
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


class LookupPostView(APIView):
    def post(self, request):
        return Response("POST_OK", status=200)

    def get(self, request):
        return Response("GET_OK", status=200)


class LookupGetView(APIView):
    def get(self, request, **kwargs):
        return Response("GET_OK", status=200)
