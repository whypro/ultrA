# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import os
import datetime
import hashlib
from bson.objectid import ObjectId
from flask import Blueprint, send_from_directory, current_app, abort, redirect
from flask import url_for
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
def show_all_topics():
    client = MongoClient()
    topic_collection = client[current_app.config['DB_NAME']]['topic']
    topics = topic_collection.find({}, {'title'})
    return render_template('list_topics.html', topics=topics)


@frontend.route('/topic/<oid>/')
def show_topic(oid):
    client = MongoClient()
    topic_collection = client[current_app.config['DB_NAME']]['topic']
    image_collection = client[current_app.config['DB_NAME']]['image']
    topic = topic_collection.find_one({'_id': ObjectId(oid)})
    images = image_collection.find({'_id': {'$in': [image for image in topic['images']]}})
    print(images.count())
    if not topic:
        abort('404')
    return render_template('show_topic.html', topic=topic, images=images)



@frontend.route('/admin/import/')
def import_all():
    # TODO: 画出活动图
    path = current_app.config['MEDIA_PATH']
    client = MongoClient()
    topic_collection = client[current_app.config['DB_NAME']]['topic']
    image_collection = client[current_app.config['DB_NAME']]['image']

    dirs = os.listdir(path)
    for tag in dirs:    # 遍历分类
        rel_tag_path = tag
        tag_path = os.path.join(path, tag)
        if os.path.isdir(tag_path):
            print(tag)
            # print(tag_path)
            topics = os.listdir(tag_path)
            for topic in topics:    # 遍历主题
                rel_topic_path = os.path.join(rel_tag_path, topic)
                topic_path = os.path.join(tag_path, topic)
                if os.path.isdir(topic_path):
                    print(topic)
                    # print(topic_path)
                    topic_data = {
                        'title': topic,
                        'time': datetime.datetime.utcnow(),
                    }
                    topic_collection.update({'title': topic}, topic_data, upsert=True)
                    images = os.listdir(topic_path)
                    for image in images:    # 遍历图片
                        rel_image_path = os.path.join(rel_topic_path, image)
                        image_path = os.path.join(topic_path, image)
                        if os.path.isfile(image_path):
                            print(rel_image_path)   
                            
                            # 存入 MongoDB
                            if image_collection.find({'path': rel_image_path}).count():
                                pass
                            else:
                                image_sha1 = hashlib.sha1(open(image_path, 'rb').read()).hexdigest()
                                print(image_sha1)
                                image_data = {
                                    'sha1': image_sha1,
                                    'path': rel_image_path,
                                }
                                image_collection.update({'path': rel_image_path}, image_data, upsert=True)
                            image_id = image_collection.find_one({'path': rel_image_path}, {'_id': True}).get('_id')
                            topic_collection.update({'title': topic}, {'$addToSet': {'images': image_id}})
                            # image_collection.insert(image_data)
                            
    return 'Import finished.'

@frontend.route('/image/<oid>/')
def show_image(oid):
    client = MongoClient()
    image_collection = client[current_app.config['DB_NAME']]['image']
    image = image_collection.find_one({'_id': ObjectId(oid)})    
    return send_from_directory(
        current_app.config['MEDIA_PATH'],
        filename=image['path']
    )

