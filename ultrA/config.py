# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import os
import platform


# FLASK
DEBUG = True
SECRET_KEY = 'I love you.'

# FLASK-THEMES
DEFAULT_THEME = 'sonja'

# MONGODB
DB_NAME = 'ultrA'
#TOPIC_COLLECTION = 'raw_topic'
#IMAGE_COLLECTION = 'raw_image'
TOPIC_COLLECTION = 'test_topic'
IMAGE_COLLECTION = 'test_image'
DISCARDED_IMAGE_COLLECTION = 'discarded_image'

if 'Windows' in platform.system():
    # MEDIA_PATH = 'I:\\一些资料\\【图片】\\【互联网图片】\\'
    # MEDIA_PATH = 'F:\\apple\\results\\'
    MEDIA_PATH = 'E:\\test\\'
else:
    # MEDIA_PATH = '/var/run/media/whypro/4. Backups/apple/autoed/'
    MEDIA_PATH = '/var/run/media/whypro/My Book/一些资料/【图片】/【互联网图片】/'

IMAGES = ('jpg', 'jpe', 'jpeg', 'png', 'gif', 'svg', 'bmp')

