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
    return redirect(url_for('.show_all_topics'))


@home.route('/topic/', defaults={'page': 1})
@home.route('/topic/<int:page>/')
@home.route('/topic/tag/<tag>/', defaults={'page': 1})
@home.route('/topic/tag/<tag>/<int:page>/')
def show_all_topics(page, tag=None):
    """Topics page.

    show all topics.

    Args:
        tag: filter by tag, if tag == None, then return all topics

    Returns:
        topics: a list of topics
        tag: same to the arg tag
    """
    db = MongoDB()
    tags = db.topic_collection.distinct('tags')
    if tag and tag not in tags:
        abort(404)

    condition = {'deleted': {'$ne': True}}
    if tag in tags:
        condition['tags'] = tag
    topics = db.topic_collection.find(
        condition,
        {'title': True, 'images': True, 'tags': True, 'rating': True}
    ).sort([
        #('click_count', 1),
        ('rating', 1),
        ('_id', -1)
    ]).skip((page-1)*current_app.config['TOPICS_PER_PAGE']).limit(current_app.config['TOPICS_PER_PAGE'])

    count = topics.count(with_limit_and_skip=True)
    total = topics.count()

    if not count:
        abort(404)

    pagination = dict(page=page, pages=total//current_app.config['TOPICS_PER_PAGE']+1)

    return render_template('home/topics.html', topics=topics_filter(topics), tag=tag, pagination=pagination)


@home.route('/_topic/')
@home.route('/_topic/tag/<tag>/')
def get_topics(tag=None):
    start = int(request.args.get('start', '0'))
    count = int(request.args.get('count', '20'))
    db = MongoDB()
    condition = {'deleted': {'$ne': True}}
    if tag:
        condition['tags'] = tag
    topics = db.topic_collection.find(
        condition, {'title': True, 'images': True, 'tags': True, 'rating': True}
    ).sort([
        ('rating', 1),
        ('_id', -1)
    ]).skip(start).limit(count)
    count = topics.count(with_limit_and_skip=True)
    total = topics.count()
    # total = db.topic_collection.find(condition).count()
    # start, count, total

    return jsonify(
        start=start, count=count, total=total,
        topics=topics_filter(topics),
    )


@home.route('/topic/hot/', defaults={'page': 1})
@home.route('/topic/hot/<int:page>/')
def show_hot_topics(page):
    db = MongoDB()
    topics = db.topic_collection.find(
        {'deleted': {'$ne': True}, 'rating': {'$gt': 0}},
        {'title': True, 'images': True, 'tags': True, 'rating': True}
    ).sort([
        ('rating', -1),
        ('click_count', -1)
    ]).skip((page-1)*current_app.config['TOPICS_PER_PAGE']).limit(current_app.config['TOPICS_PER_PAGE'])

    count = topics.count(with_limit_and_skip=True)
    total = topics.count()

    if not count:
        abort(404)

    pagination = dict(page=page, pages=total//current_app.config['TOPICS_PER_PAGE']+1)

    return render_template('home/topics.html', topics=topics_filter(topics), pagination=pagination)


def topics_filter(origin_topics):
    topics = []
    # 重新包装
    for topic in origin_topics:
        _id = str(topic['_id'])
        title = topic['title']
        size = len(topic['images'])
        cover = str(topic['images'][0]) if size else ''
        tag = topic['tags'][0] if len(topic['tags']) else None
        rating = topic.get('rating', 0)
        # print(rating)
        topics.append(dict(_id=_id, title=title, size=size, cover=cover, tag=tag, rating=rating))
    return topics


@home.route('/topic/search/')
def search():
    key = request.args.get('key')
    print(key)
    key_regex = re.compile(key, re.IGNORECASE)
    db = MongoDB()
    topics = db.topic_collection.find({'deleted': {'$ne': True}, 'title': key_regex}).limit(50)
    return render_template('home/topics.html', topics=topics_filter(topics))


@home.route('/topic/<oid>/')
def show_topic(oid):
    db = MongoDB()
    topic = db.topic_collection.find_one({'_id': ObjectId(oid)})
    if not topic:
        abort(404)
    rating = topic.get('rating')
    images = db.image_collection.find({'_id': {'$in': list(topic['images'])}})
    print(images.count())
    db.topic_collection.update({'_id': ObjectId(oid)}, {'$inc': {'click_count': 1}})
    # 为游标增加字段
    images = list(images)
    for image in images:
        if db.garbage_image_collection.find_one({'sha1': image['sha1']}):
            image['garbage'] = True
        else: 
            image['garbage'] = False
    print(len(images))
    return render_template('home/topic_detail.html', topic=topic, images=images, rating=rating)


@home.route('/image/<oid>/show/')
def show_image(oid):
    db = MongoDB()
    image = db.image_collection.find_one({'_id': ObjectId(oid)})
    return render_template('home/image_detail.html', image=image)


@home.route('/image/<size>/<oid>/')
def send_image(size, oid):
    if size not in ('origin', 'large', 'thumb'):
        abort(404)
    db = MongoDB()
    image = db.image_collection.find_one({'_id': ObjectId(oid)})
    if not image:
        abort(404)
    path = os.path.join(current_app.config['MEDIA_PATH'], image['path'])
    # directory = os.path.dirname(path)
    # filename = os.path.basename(path)
    if size == 'origin':
        print('directly send file.')
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


@home.route('/image/<oid>/_discard/', methods=['POST'])
def discard_image(oid):
    db = MongoDB()
    image = db.image_collection.find_one({'_id': ObjectId(oid)})
    if not image:
        return jsonify(error=404)
    db.garbage_image_collection.update({'sha1': image['sha1']}, {'sha1': image['sha1']}, upsert=True)
    return jsonify({})


@home.route('/topic/<oid>/_delete/', methods=['POST'])
def delete_topic(oid):
    # 获取删除参数
    if request.form.get('physical_removal') == 'true':
        physical_removal = True
    else:
        physical_removal = False
    if request.form.get('remove_images') == 'true':
        remove_images = True
    else:
        remove_images = False

    print(physical_removal, remove_images)
    delete_topic_(oid, physical_removal, remove_images)
    return jsonify({})


def delete_topic_(oid, physical_removal=False, remove_images=True):
    # remove_local = request.form.get('remove_local')
    db = MongoDB()
    topic = db.topic_collection.find_one({'_id': ObjectId(oid)})
    if not topic:
        return jsonify(error=404)
    if remove_images:
        first_image = db.image_collection.find_one({'_id': {'$in': topic['images']}})
        # 删除图片目录
        if first_image:
            topic_path = os.path.dirname(os.path.join(current_app.config['MEDIA_PATH'], first_image['path']))
            print(topic_path)
            if os.path.exists(topic_path):
                shutil.rmtree(topic_path)
        # 删除所有图片
        db.image_collection.remove({'_id': {'$in': topic['images']}})
    if physical_removal:
        db.topic_collection.remove({'_id': ObjectId(oid)})
    else:
        # 标记主题为已删除
        db.topic_collection.update(
            {'_id': ObjectId(oid)},
            {'$set': {'deleted': True, 'modify_time': datetime.utcnow()}}
        )


@home.route('/topic/<oid>/_edit/', methods=['POST'])
def edit_topic(oid):
    title = request.form.get('title')
    rating = request.form.get('rating')
    
    if rating in ('1', '2', '3', '4', '5'):
        rating = int(rating)
    elif rating:
        abort(400)

    db = MongoDB()
    set_data = {'modify_time': datetime.utcnow()}
    if title:
        set_data['title'] = title
    if rating:
        set_data['rating'] = rating
    print(set_data)
    db.topic_collection.update({'_id': ObjectId(oid)}, {'$set': set_data})
    # topic = db.topic_collection.find_one({'_id': ObjectId(oid)}, {'title': True, 'rating': True})
    return jsonify(set_data, success=True)


