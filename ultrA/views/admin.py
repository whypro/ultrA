# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import os
import hashlib
from flask import Blueprint, abort, current_app
from pymongo import MongoClient
from ultrA.helpers import render_template


admin = Blueprint('admin', __name__)


@admin.route('/admin/import/')
def show_import():
    return render_template('admin/show_import.html')


@admin.route('/admin/import/<int:option>/')
def import_all(option):
    if option not in (0, 1, 2):
        abort(404)
    
    path = current_app.config['MEDIA_PATH']
    client = MongoClient()
    topic_collection = client[current_app.config['DB_NAME']][current_app.config['TOPIC_COLLECTION']]
    image_collection = client[current_app.config['DB_NAME']][current_app.config['IMAGE_COLLECTION']]
    import_topics_and_images(path, topic_collection, image_collection, option)
                  
    return 'Import finished.'


@admin.route('/admin/remove/')
def remove_all():
    client = MongoClient()
    topic_collection = client[current_app.config['DB_NAME']][current_app.config['TOPIC_COLLECTION']]
    image_collection = client[current_app.config['DB_NAME']][current_app.config['IMAGE_COLLECTION']]
    topic_collection.remove()
    image_collection.remove()
    return 'Removed.'


def import_topics_and_images(path, topic_collection, image_collection, option=0):
    """
        option == 0 or others: 略过已存在记录
        option == 1: 更新已存在记录
        option == 2: 重建已存在记录
    """
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

                    topic_found = topic_collection.find_one({'title': topic})
                    if (not topic_found) or (topic_found and option in (1, 2)):     # 需要更新主题
                        if topic_found and option == 1:     # 更新已存在的记录
                            topic_data = {
                                '$set': {
                                    'tags': [tag],
                                }
                            }
                            print('update image...')
                            topic_collection.update({'title': topic}, topic_data)
                        elif topic_found and option == 2:   # 重建已存在的记录
                            topic_data = {
                                'title': topic,
                                'tags': [tag],
                            }
                            print('reset image...')
                            topic_collection.update({'title': topic}, topic_data)
                        elif not topic_found:   # not found, insert
                            topic_data = {
                                'title': topic,
                                'tags': [tag],
                            }
                            print('insert image...')
                            topic_collection.insert(topic_data)

                        images = os.listdir(topic_path)
                        for image in images:    # 遍历图片
                            rel_image_path = os.path.join(rel_topic_path, image)
                            image_path = os.path.join(topic_path, image)
                            # print(image.split('.')[-1].lower())
                            if os.path.isfile(image_path) and image.split('.')[-1].lower() in current_app.config['IMAGES']:
                                print(rel_image_path)

                                image_found = image_collection.find_one({'path': rel_image_path})
                                # 存入 MongoDB
                                if image_found and option == 1:     # 更新已存在的图片
                                    image_data = {
                                        '$set': {}
                                    }
                                    print('update topic...')
                                    image_collection.update({'path': rel_image_path}, image_data)
                                elif image_found and option == 2:   # 重建已存在的图片
                                    image_sha1 = hashlib.sha1(open(image_path, 'rb').read()).hexdigest()
                                    print(image_sha1)
                                    image_data = {
                                        'sha1': image_sha1,
                                        'path': rel_image_path,
                                    }
                                    print('reset topic...')
                                    image_collection.update({'path': rel_image_path}, image_data)
                                elif not image_found:
                                    image_sha1 = hashlib.sha1(open(image_path, 'rb').read()).hexdigest()
                                    print(image_sha1)
                                    image_data = {
                                        'sha1': image_sha1,
                                        'path': rel_image_path,
                                    }
                                    print('insert topic...')
                                    image_collection.insert(image_data)

                                image_id = image_collection.find_one({'path': rel_image_path}, {'_id': True}).get('_id')
                                topic_collection.update({'title': topic}, {'$addToSet': {'images': image_id}})
