import os
from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser
from observation import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from utils import utils
from skvo import settings
from uuid import uuid4

from datapipe.photometry import transform
from datapipe.photometry import filesystem

from rest_framework import generics
from observation import models

import logging
logger = logging.getLogger("observation.view")
# Create your views here.


class PhotometryList(generics.ListCreateAPIView):
    queryset = models.Photometry.objects.all()

    def get_serializer_class(self):
        serializer_class = serializers.PhotometrySerializer
        if self.request.method in ["POST"]:
            serializer_class = serializers.PhotometryCreateManySerializer
        return serializer_class


def get_uploaded_mediafile_content(request):
    f = request.data["file"]
    bytes_reader = f.file
    msg_content = transform.decode_avro_message(bytes_reader)
    msg_content = transform.avro_raw_deserializer(msg_content)
    return msg_content


def check_medidafile_crc(msg_content):
    if not utils.check_md5_crc(msg_content["content"], msg_content["md5_crc"]):
        raise ParseError("Invalid crc - probably corrupted file")


def get_mediafile_dir(msg_content):
    return filesystem.get_media_path_from_metadata(
        target=msg_content["target"], base_path=settings.SKVO_EXPORT_PATH,
        source=msg_content["source"], bandpass=msg_content["bandpass"], start_date=msg_content["start_date"],
    )


class PhotometryMedia(APIView):
    parser_classes = (FileUploadParser, )

    def post(self, request, *args, **kwargs):
        if 'file' not in request.data:
            raise ParseError("Empty content")

        logger.debug("Getting message content of upload".format(request.data["file"]))
        msg_content = get_uploaded_mediafile_content(request)
        logger.debug("Checking mediafile crc")
        check_medidafile_crc(msg_content)
        media_dir_path = get_mediafile_dir(msg_content)
        mediafile_path = os.path.join(media_dir_path, msg_content["filename"])

        logger.debug("Creating path: {}".format(media_dir_path))
        filesystem.create_media_path_if_needed(media_dir_path)
        logger.debug("Checking whether file exists")

        if os.path.isfile(mediafile_path):
            existing_file_content = filesystem.read_file_as_binary(mediafile_path)
            existing_file_crc = utils.md5_raw_content(existing_file_content)

            if existing_file_crc == msg_content["md5_crc"]:
                logger.info("File w/ same CRC already exists, skipping")
                return Response(dict(msg="File w/ same CRC already exists, skipping"), status=200)
            else:
                msg_content["filename"] = "{}.{}".format(msg_content["filename"], str(uuid4()))
                logger.warning("File w/ same filename already exists, but CRC differ. Saving new file as {}"
                               "".format(msg_content["filename"]))
                mediafile_path = os.path.join(media_dir_path, msg_content["filename"])

        logger.debug("Decompressing file")
        msg_content["content"] = utils.decompress(msg_content["content"])
        logger.info("Saving {}".format(mediafile_path))
        try:
            filesystem.write_file_as_binary(mediafile_path, msg_content["content"])
        except Exception as e:
            logger.error("{}".format(str(e)))
            return Response(dict(msg=str(e)), status=500)
        return Response(dict(msg="created"), status=201)

