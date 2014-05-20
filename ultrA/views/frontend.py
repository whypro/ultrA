# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import os
import shutil
from bson.objectid import ObjectId
from flask import Blueprint, send_from_directory, current_app, abort, redirect
from flask import url_for, request, jsonify
from pymongo import MongoClient
from ultrA.helpers import render_template


frontend = Blueprint('frontend', __name__)


@frontend.route('/favicon.ico')
def favicon():
    return send_from_directory(
        'static',
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


@frontend.route('/')
def index():
    return redirect(url_for('.show_all_topics'))


@frontend.route('/topic/')
@frontend.route('/topic/tag/<tag>/')
def show_all_topics(tag=None):
    client = MongoClient()
    topic_collection = client[current_app.config['DB_NAME']][current_app.config['TOPIC_COLLECTION']]
    tags = topic_collection.distinct('tags')
    if tag and tag not in tags:
        abort(404)

    condition = {'deleted': {'$ne': True}}
    if tag in tags:
        condition['tags'] = tag
    topics = topic_collection.find(
        condition,
        {'title': True, 'images': True, 'tags': True}
    ).sort([
        #('click_count', 1),
        ('rate', 1),
        ('_id', -1)
    ]).limit(50)

    return render_template(
        'frontend/list_topics.html',
        topics=[dict(_id=str(topic['_id']), title=topic['title'], cover=str(topic['images'][0]), size=len(topic['images']), tag=topic['tags'][0]) for topic in topics],
    )


@frontend.route('/_topic/')
@frontend.route('/_topic/tag/<tag>/')
def get_topics(tag=None):
    start = request.args.get('start', 0)
    count = request.args.get('count', 20)
    client = MongoClient()
    topic_collection = client[current_app.config['DB_NAME']][current_app.config['TOPIC_COLLECTION']]
    condition = {'deleted': {'$ne': True}}
    if tag:
        condition['tags'] = tag
    topics = topic_collection.find(
        condition, {'title': True, 'images': True, 'tags': True}
    ).sort([
        ('rate', 1),
        ('_id', -1)
    ]).skip(start).limit(count)
    count = topics.count()
    total = topic_collection.find().count()
    # start, count, total

    return jsonify(
        start=start, count=count, total=total,
        topics=[dict(_id=str(topic['_id']), title=topic['title'], cover=str(topic['images'][0]), size=len(topic['images']), tag=topic['tags'][0]) for topic in topics],
    )


@frontend.route('/topic/<oid>/')
def show_topic(oid):
    client = MongoClient()
    topic_collection = client[current_app.config['DB_NAME']][current_app.config['TOPIC_COLLECTION']]
    image_collection = client[current_app.config['DB_NAME']][current_app.config['IMAGE_COLLECTION']]
    topic = topic_collection.find_one({'_id': ObjectId(oid)})
    if not topic:
        abort(404)
    rate = topic.get('rate')
    images = image_collection.find({'_id': {'$in': list(topic['images'])}})
    print(images.count())
    topic_collection.update({'_id': ObjectId(oid)}, {'$inc': {'click_count': 1}})
    return render_template('frontend/show_topic.html', topic=topic, images=images, rate=rate)


@frontend.route('/image/<oid>/')
def show_image(oid):
    client = MongoClient()
    image_collection = client[current_app.config['DB_NAME']][current_app.config['IMAGE_COLLECTION']]
    image = image_collection.find_one({'_id': ObjectId(oid)})
    if not image:
        abort(404)
    path = os.path.join(current_app.config['MEDIA_PATH'], image['path'])
    directory = os.path.dirname(path)
    filename = os.path.basename(path)

    # from PIL import Image
    # size = 400, 400
    # im = Image.open(path)
    # im.thumbnail(size, Image.ANTIALIAS)
    # im.save('D:\\temp.jpg')
    # return send_from_directory('D:\\', 'temp.jpg')

    return send_from_directory(directory, filename)


@frontend.route('/image/<oid>/_discard/', methods=['GET'])
def discard_image(oid):
    client = MongoClient()
    image_collection = client[current_app.config['DB_NAME']][current_app.config['IMAGE_COLLECTION']]
    discarded_image_collection = client[current_app.config['DB_NAME']][current_app.config['DISCARDED_IMAGE_COLLECTION']]
    image = image_collection.find_one({'_id': ObjectId(oid)})
    if not image:
        return jsonify(error=404)
    discarded_image_collection.update({'sha1': image['sha1']}, {'sha1': image['sha1']}, upsert=True)
    return jsonify({})

@frontend.route('/topic/<oid>/_delete/', methods=['POST'])
def delete_topic(oid):
    # remove_local = request.form.get('remove_local')
    client = MongoClient()
    topic_collection = client[current_app.config['DB_NAME']][current_app.config['TOPIC_COLLECTION']]
    image_collection = client[current_app.config['DB_NAME']][current_app.config['IMAGE_COLLECTION']]
    topic = topic_collection.find_one({'_id': ObjectId(oid)})
    if not topic:
        return jsonify(error=404)
    first_image = image_collection.find_one({'_id': {'$in': topic['images']}})
    # 删除图片目录
    if first_image:
        topic_path = os.path.dirname(os.path.join(current_app.config['MEDIA_PATH'], first_image['path']))
        print(topic_path)
        if os.path.exists(topic_path):
            shutil.rmtree(topic_path)
    # 删除所有图片
    image_collection.remove({'_id': {'$in': topic['images']}})
    # 标记主题为已删除
    topic_collection.update({'_id': ObjectId(oid)}, {'$set': {'deleted': True}})
    return jsonify({})


@frontend.route('/topic/<oid>/_edit/', methods=['POST'])
def edit_topic(oid):
    title = request.form.get('title')
    rate = request.form.get('rate')
    
    if rate in ('1', '2', '3', '4', '5'):
        rate = int(rate)
    elif rate:
        abort(400)

    client = MongoClient()
    topic_collection = client[current_app.config['DB_NAME']][current_app.config['TOPIC_COLLECTION']]
    set_data = {}
    if title:
        set_data['title'] = title
    if rate:
        set_data['rate'] = rate
    print(set_data)
    topic_collection.update({'_id': ObjectId(oid)}, {'$set': set_data})
    # topic = topic_collection.find_one({'_id': ObjectId(oid)}, {'title': True, 'rate': True})
    return jsonify(set_data, success=True)

