# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
from datetime import datetime
import os
from StringIO import StringIO

from bson.objectid import ObjectId
from flask import Blueprint, current_app, abort, send_file
from flask import jsonify
from PIL import Image

from ..helpers import render_template
from ..database import MongoDB


photo = Blueprint('photo', __name__, url_prefix='/photo')

@photo.route('/<oid>/<size>/')
def send_image(size, oid):
    if size not in ('origin', 'large', 'thumb'):
        abort(400)
    db = MongoDB()
    image = db.photos.find_one({'_id': ObjectId(oid)})
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


@photo.route('/show/<oid>/')
def show_photo_detail(oid):
    db = MongoDB()
    photo = db.photos.find_one({'_id': ObjectId(oid)})
    return render_template('photo/photo_detail.html', photo=photo)


@photo.route('/<oid>/_blur/', methods=['POST'])
def ajax_blur_photo(oid):
    """将图片标记为垃圾图片"""
    db = MongoDB()
    photo = db.photos.find_one({'_id': ObjectId(oid)})
    if not photo:
        return jsonify(status=404)
    db.photos.update({'sha1': photo['sha1']}, {'$set': {'blur': True}}, multi=True)
    db.blurs.update({'sha1': photo['sha1']}, {'sha1': photo['sha1']}, upsert=True)
    return jsonify(status=200)
