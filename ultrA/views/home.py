# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division
from datetime import datetime
import os
import shutil
import re
from StringIO import StringIO
from bson.objectid import ObjectId
from flask import Blueprint, send_from_directory, current_app, abort, redirect, send_file
from flask import url_for, request, jsonify
from PIL import Image
from ultrA.helpers import render_template
from ultrA.database import MongoDB


home = Blueprint('home', __name__)


@home.route('/favicon.ico')
def favicon():
    # return send_from_directory('static', 'favicon.ico')
    return send_file('static/favicon.ico')


@home.route('/')
def index():
    return redirect(url_for('topic.show_topics'))

