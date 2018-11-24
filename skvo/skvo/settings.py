"""
Django settings for skvo project.

Generated by 'django-admin startproject' using Django 2.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import logging
from configparser import ConfigParser
from pyopentsdb import tsdb

# quick log settings
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s : [%(levelname)s] : %(name)s : %(message)s')
logger = logging.getLogger(__name__)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# config

env_variable_config = os.environ.get('SKVO_CONFIG', '')
venv_config = os.path.join(os.environ.get('VIRTUAL_ENV', ''), 'conf', 'skvo.ini')

if os.path.isfile(env_variable_config):
    config_file = env_variable_config
elif os.path.isfile(venv_config):
    config_file = venv_config
else:
    raise LookupError("Couldn't resolve configuration file. To define it \n "
                      "  - Set the environment variable SKVO_CONFIG, or \n "
                      "  - add conf/skvo.ini under your virtualenv root\n")

config = ConfigParser(defaults={
    'config': '',
})
logger.info("Parse config file: {}".format(venv_config))
config.read(config_file)

SKVO_BASE_PATH = config.get("general", "base_path")
SKVO_EXPORT_PATH = config.get("general", "export_path")

OPENTSDB_SERVER = config.get("opentsdb", "server")
TSDB_CONNECTOR = tsdb.tsdb_connection(host=OPENTSDB_SERVER)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECRET_KEY = '(yty%gzc4x7(12$h@tnzgv(fb-3_cp*r0y%6i3uis^b61g+ppy'

SECRET_KEY = config.get('secret', 'secret_key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config.get('django', 'debug').lower() == 'true'

if DEBUG:
    ALLOWED_HOSTS = []
else:
    ALLOWED_HOSTS = [host.strip() for host in config.get('django', 'allowed_hosts').split(',')]

STATIC_URL = '/skvo_static/'
if config.get('django', 'static_root'):
    STATIC_ROOT = config.get('django', 'static_root')
else:
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_URL = '/skvo_media/'
if config.get('django', 'media_root'):
    MEDIA_ROOT = config.get('django', 'media_root')
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'observation.apps.ObservationConfig',
    'lookup.apps.LookupConfig',
    'datapipe.apps.DatapipeConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'skvo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'skvo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': config.get('database', 'engine'),
        'NAME': config.get('database', 'name'),
        'USER': config.get('database', 'user'),
        'HOST': config.get('database', 'host'),
        'PORT': config.get('database', 'port'),
        'PASSWORD': config.get('database', 'password'),
        'DEFAULT_CHARSET': config.get('database', 'default_character_set'),
        'TIME_ZONE': "UTC",
        'OPTIONS': {
            'init_command': 'SET default_storage_engine=INNODB',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

