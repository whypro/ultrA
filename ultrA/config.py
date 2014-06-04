# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import os
import platform


class Config(object):
    # FLASK

    # FLASK-THEMES
    DEFAULT_THEME = 'semantic'

    # MONGODB
    DB_HOST = 'localhost'
    DB_NAME = 'ultrA'
    DB_USERNAME = 'whypro'
    DB_PASSWORD = 'whypro'
    DB_PORT = 27017

    TOPIC_COLLECTION = 'raw_topic'
    IMAGE_COLLECTION = 'raw_image'
    GARBAGE_IMAGE_COLLECTION = 'raw_garbage_image'
    # TOPIC_COLLECTION = 'test_topic'
    # IMAGE_COLLECTION = 'test_image'
    # DISCARDED_IMAGE_COLLECTION = 'test_discarded_image'

    IMAGES = ('jpg', 'jpe', 'jpeg', 'png', 'gif', 'svg', 'bmp')
    IMAGE_THUMB = 320
    IMAGE_LARGE = 1024


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = 'I love you.'
    if 'Windows' in platform.system():
        # MEDIA_PATH = 'I:\\一些资料\\【图片】\\【互联网图片】\\'
        MEDIA_PATH = 'F:\\apple\\results\\'
        # MEDIA_PATH = 'E:\\test\\'
    else:
        # MEDIA_PATH = '/var/run/media/whypro/4. Backups/apple/autoed/'
        # MEDIA_PATH = '/var/run/media/whypro/My Book/一些资料/【图片】/【互联网图片】/'
        MEDIA_PATH = '/var/run/media/whypro/4. Backups/apple/results/'


