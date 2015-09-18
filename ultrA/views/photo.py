# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
from datetime import datetime
import os
import shutil
import re
from StringIO import StringIO

from bson.objectid import ObjectId
from flask import Blueprint, send_from_directory, current_app, abort, redirect, send_file
from flask import url_for, request, jsonify
from PIL import Image

from ..helpers import render_template
from ..database import MongoDB


photo = Blueprint('photo', __name__, url_prefix='/photo')

@photo.route('/<size>/<oid>/')
def send_image(size, oid):
    if size not in ('origin', 'large', 'thumb'):
        abort(400)
    db = MongoDB()
    image = db.image_collection.find_one({'_id': ObjectId(oid)})
    if not image:
        abort(404)
    path = os.path.join(current_app.config['MEDIA_PATH'], image['path'])
    # directory = os.path.dirname(path)
    # filename = os.path.basename(path)
    if size == 'origin':
        print 'directly send file.'
        return send_file(path)
    else:   # image_type != 'origin'
        # 生成缩略图
        f = open(path, 'rb')
        try:
            img = Image.open(f)
        except IOError:
            f.close()
            raise
        # 如果是 GIF，则不处理
        if img.format == 'GIF':
            return send_file(path, mimetype='image/'+img.format.lower())
        size_dict = {
            'thumb': current_app.config['IMAGE_THUMB'],
            'large': current_app.config['IMAGE_LARGE'],
        }
        width = size_dict[size]
        height = (width*img.size[1]) // img.size[0]
        img.thumbnail((width, height), Image.ANTIALIAS)
        img_io = StringIO()
        if img.format == 'JPEG':
            img.save(img_io, img.format, quality=70)
        else:
            print(img.format)
            img.save(img_io, img.format)
        f.close()
        img_io.seek(0)
        return send_file(img_io, mimetype='image/'+img.format.lower())
