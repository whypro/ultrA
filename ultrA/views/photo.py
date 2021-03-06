# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
import datetime
import os
from StringIO import StringIO

from bson.objectid import ObjectId
from flask import Blueprint, current_app, abort, send_file
from flask import jsonify
from PIL import Image

from ..helpers import render_template
from ..extensions import db


photo = Blueprint('photo', __name__, url_prefix='/photo')

@photo.route('/<oid>/<size>/')
def send_image(size, oid):
    if size not in ('origin', 'large', 'thumb'):
        abort(400)
    image = db.photos.find_one({'_id': ObjectId(oid)})
    if not image:
        abort(404)
    path = os.path.join(current_app.config['MEDIA_PATH'], image['path'])
    # directory = os.path.dirname(path)
    # filename = os.path.basename(path)
    if size == 'origin':
        print 'directly send file.'
        return send_file(path)

    # image_type != 'origin'
    # 生成缩略图
    with open(path, 'rb') as f:
        # try
        img = Image.open(f)

        # 如果是 GIF，则不处理
        if img.format == 'GIF':
            return send_file(path, mimetype='image/'+img.format.lower())
        size_dict = {
            'thumb': current_app.config['IMAGE_THUMB'],
            'large': current_app.config['IMAGE_LARGE'],
        }
        width = size_dict[size]
        height = (width*img.size[1]) // img.size[0]
        img_io = StringIO()
        # try
        img.thumbnail((width, height), Image.ANTIALIAS)

        if img.format == 'JPEG':
            img.save(img_io, img.format, quality=70)
        else:
            print(img.format)
            img.save(img_io, img.format)
        # img_io.close()
        f.close()
        img_io.seek(0)
        return send_file(img_io, mimetype='image/'+img.format.lower())


@photo.route('/show/<oid>/')
def show_photo_detail(oid):
    photo = db.photos.find_one({'_id': ObjectId(oid)})
    return render_template('photo/photo_detail.html', photo=photo)


@photo.route('/<oid>/_blur/', methods=['POST'])
def ajax_blur_photo(oid):
    """将图片标记为垃圾图片"""
    if blur_photo(ObjectId(oid)):
        status = 200
    else:
        status = 404
    return jsonify(status=status)


def blur_photo(oid):
    photo = db.photos.find_one({'_id': oid})
    if not photo:
        return False

    db.photos.update({'sha1': photo['sha1']}, {'$set': {'blur': True}}, multi=True)
    db.blurs.update({'sha1': photo['sha1']}, {'sha1': photo['sha1']}, upsert=True)

    # 标记所有相关主题重新计算相关度和纯净度
    photos = db.photos.find({'sha1': photo['sha1']}, {'topic': True})
    topic_oids = set([p['topic'] for p in photos if 'topic' in p])  # 去重
    for topic_oid in topic_oids:
        db.topics.update({'_id': topic_oid}, {'$set': {'similarity_calculated': False, 'purity_calculated': False, 'modify_time': datetime.datetime.utcnow()}})

    return True
