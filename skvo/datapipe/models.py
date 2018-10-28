from django.db import models

# Create your models here.

MODEL_FIELDS = ['id', 'filename', 'md5', 'content']


class UploadModelLess(object):
    def __init__(self, **kwargs):
        for field in MODEL_FIELDS:
            setattr(self, field, kwargs.get(field, None))
