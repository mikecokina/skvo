from rest_framework.views import APIView
from rest_framework.response import Response
from utils import post
from datapipe import upload

import logging
# Create your views here.


class Upload(APIView):
    @staticmethod
    def validate_data(post_data):
        # todo: add validation logic here
        return post_data

    def post(self, request):
        post_data = post.get_post_data(request)
        validated_data = self.validate_data(post_data)
        import_status = upload.imp(validated_data)

        # todo: add response logic here
        return Response(post_data)
