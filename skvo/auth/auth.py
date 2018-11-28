from configparser import ConfigParser

from rest_framework import authentication
from rest_framework import exceptions
from skvo import settings


class SkvoAuthUser(object):
    def __init__(self, username):
        self.is_authenticated = True
        self.username = username
        self.password = None


class SkvoBasicAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        username = request.META.get("HTTP_USERNAME")
        password = request.META.get("HTTP_PASSWORD")

        if not username:
            return None
        try:
            config = ConfigParser(defaults={
                'config': '',
            })
            config.read(settings.config_file)

            if username == config.get("auth", "username") and password == config.get("auth", "password"):
                user = SkvoAuthUser(username=username)
                return user, None
        except:
            raise exceptions.AuthenticationFailed('Incorrect ')
