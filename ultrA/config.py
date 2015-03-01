# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import os
import platform


class Config(object):
    # FLASK

    # FLASK-THEMES
    DEFAULT_THEME = 'semantic_ui'

    # MONGODB
    DB_HOST = 'localhost'
    DB_NAME = 'ultrA'
    DB_USERNAME = 'whypro'
    DB_PASSWORD = 'whypro'
    DB_PORT = 27017

    IMAGES = ('jpg', 'jpe', 'jpeg', 'png', 'gif', 'svg', 'bmp')
    IMAGE_THUMB = 320
    IMAGE_LARGE = 1024


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = 'I love you.'


class NormalConfig(DevelopmentConfig):
    TOPIC_COLLECTION = 'test_topic'
    IMAGE_COLLECTION = 'test_image'
    GARBAGE_IMAGE_COLLECTION = 'test_garbage_image'
    
    if 'Windows' in platform.system():
        MEDIA_PATH = 'E:\\照片'
    else:
        MEDIA_PATH = '/var/run/media/whypro/4. Backups/apple/autoed/'


class UltrAConfig(DevelopmentConfig):
    TOPIC_COLLECTION = 'raw_topic'
    IMAGE_COLLECTION = 'raw_image'
    GARBAGE_IMAGE_COLLECTION = 'raw_garbage_image'
    if 'Windows' in platform.system():
        MEDIA_PATH = 'J:\\一些资料\\apple\\results'
    else:
        MEDIA_PATH = '/var/run/media/whypro/4. Backups/apple/results/'


class TestingConfig(UltrAConfig):
    TESTING = True
    CSRF_ENABLED = False

