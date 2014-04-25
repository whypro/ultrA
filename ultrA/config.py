# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import os
import platform


# FLASK
DEBUG = True
SECRET_KEY = 'I love you.'

# FLASK-THEMES
DEFAULT_THEME = 'default'

# MONGODB
DB_NAME = 'ultrA'

if 'Windows' in platform.system():
    MEDIA_PATH = 'F:\\apple\\autoed\\'
else:
    # MEDIA_PATH = '/var/run/media/whypro/4. Backups/apple/autoed/'
    MEDIA_PATH = '/var/run/media/whypro/3. Media & Files/test/'

IMAGES = ('jpg', 'jpe', 'jpeg', 'png', 'gif', 'svg', 'bmp')

