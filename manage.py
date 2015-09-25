# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys
import os

from flask.ext.script import Manager

from ultrA import create_app


app = create_app('ultrA.config.UltrAConfig')
manager = Manager(app)


@manager.command
def debug():
    """Start Server in debug mode"""
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)


if __name__ == '__main__':
    manager.run()
