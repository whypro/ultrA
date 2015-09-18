# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys
import os

from ultrA import create_app

app = create_app('ultrA.config.UltrAConfig')

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
