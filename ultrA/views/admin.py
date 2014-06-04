# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division
import os
import hashlib
from time import clock
from flask import Blueprint, abort, current_app, jsonify, redirect, url_for
from ultrA.helpers import render_template
from ultrA.database import MongoDB
from ultrA.views.frontend import delete_topic_

admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.route('/')
def index():
    return render_template('admin/index.html')


@admin.route('/import/<int:option>/')
def import_all(option):
    if option not in (0, 1, 2):
        abort(404)
    
    path = current_app.config['MEDIA_PATH']
    db = MongoDB()
    import_topics_and_images(path, db.topic_collection, db.image_collection, option)
                  
    return 'Import finished.'


@admin.route('/remove/')
def remove_all():
    db = MongoDB()
    db.topic_collection.remove()
    db.image_collection.remove()
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


@admin.route('/clean/_progress/')
def get_clean_progress():
    return jsonify(progress=current_app.clean_progress)


@admin.route('/garbage/check/')
def check_garbage():
    """
    清理主题：将所有无关图片加入黑名单内，循环搜索每个主题，
    若该主题内黑名单图片的比例大于某阈值，则将主题 garbage 标记为 True。
    """
    threshold = 0.6
    db = MongoDB()
    
    # 如果一个 topic 内图片个数为 0，直接标记
    db.topic_collection.update({'images': [], 'deleted': {'$ne': True}, 'garbage': {'$ne': True}}, {'$set': {'garbage': True}})
    
    # 如果一个 topic 内包含的 garbage_image 数大于图片个数的 1/X，删除 topic 和图片
    topics = db.topic_collection.find({'deleted': {'$ne': True}, 'garbage': {'$ne': True}})
    garbage_images = db.garbage_image_collection.find({})
    garbage_images_sha1 = [garbage_image['sha1'] for garbage_image in garbage_images]
    for topic in topics:
        images = db.image_collection.find({'_id': {'$in': list(topic['images'])}}, {'sha1': True})
        if not images.count():
            # 如果主题已没有图片，直接标记 garbage
            db.topic_collection.update({'_id': topic['_id']}, {'$set': {'garbage': True}})
            continue
        images_sha1 = [image['sha1'] for image in images]
        garbage_count = 0
        for image_sha1 in images_sha1:
            if image_sha1 in garbage_images_sha1:
                garbage_count += 1
        if garbage_count / len(images_sha1) > threshold:
            # 大于阈值，标记
            # print(topic['_id'])
            db.topic_collection.update({'_id': topic['_id']}, {'$set': {'garbage': True}})

    return redirect(url_for('.show_garbage'))


@admin.route('/garbage/')
def show_garbage():
    db = MongoDB()
    garbage_topics = db.topic_collection.find({'garbage': True})
    return render_template('admin/show_garbage.html', topics=list(garbage_topics))


@admin.route('/garbage/clean/')
def clean_garbage():
    db = MongoDB()
    garbage_topics = db.topic_collection.find({'garbage': True, 'deleted': {'$ne': True}})
    print(garbage_topics.count())
    for topic in garbage_topics:
        print(topic['_id'])
        delete_topic_(topic['_id'])
    return redirect(url_for('.show_garbage'))


@admin.route('/omission/check/')
def check_omissions():
    db = MongoDB()
    topics = db.topic_collection.find({'omitted': {'$ne': True}, 'deleted': {'$ne': True}})
    for topic in topics:
        if len(set(topic['images'])) != len(topic['images']):
            db.topic_collection.update({'_id': topic['_id']}, {'$set': {'omitted': True}})

    return redirect(url_for('.show_omissions'))


@admin.route('/omission/')
def show_omissions():
    db = MongoDB()
    omitted_topics = db.topic_collection.find({'omitted': True})
    return render_template('admin/show_omissions.html', topics=list(omitted_topics))


@admin.route('/omission/clean/')
def clean_omissions():
    db = MongoDB()
    omitted_topics = db.topic_collection.find({'omitted': True, 'deleted': {'$ne': True}})
    print(omitted_topics.count())
    for topic in omitted_topics:
        print(topic['_id'])
        delete_topic_(topic['_id'], physical_removal=True, remove_images=True)
    return redirect(url_for('.show_omissions'))


@admin.route('/all/')
def show_all():
    db = MongoDB()
    topics = db.topic_collection.find({})
    return render_template('admin/list_topics.html', topics=list(topics))



@admin.route('/duplicate/')
def clear_duplicates():
    """
    清理重复主题：在数据库中搜索包含相同图片的主题，
    可分为三种情况：
    1 A 的图片数量等于 B 的图片数量；
    1.1 A.images 包含 B.images

    # 1.1 求 A 与 B 的交集，若交集图片数量等于 A 或 B 图片的数量
    # ，或者交集图片数量大于某阈值时，则两主题相似；
    # 2 A 的图片数量小于或大于 B 的图片数量；
    # 2.1 A 与 B 的交集
    # 2. A 相等于 B
    # 3. B 真包含 A
    # 4. A 与 B 的交集图片数量大于某阈值
    """


    # 1 if 主题内 images 的 id 完全相同（爬虫时的 BUG），仅删除主题，不删除图片
    # 2 elif 主题内 images 的 path 完全相同，删除主题和主题相关的图片
    # 3 elif 主题内 images 的 sha1 完全相同，删除主题和主题相关的图片
    db = MongoDB()
    topics = db.topic_collection.find({'deleted': {'$ne': True}}, {'images': True})
    duplicates = []
    total_num = topics.count()
    begin = clock()
    # topic_ids = [topic['_id'] for topic in topics]
    # for i, topic_id in enumerate(topic_ids):
    #     topic = db.topic_collection.find_one({'_id': topic_id})
    #     for image_oid in topic['images']:
    #         image = image_collection.find_one({'_id': image_oid})
    #         image['sha1']
    #     duplicate_topics = db.topic_collection.find({'_id': {'$in': topic_ids}, 'deleted': {'$ne': True}, 'images': list(topic['images'])}, {'title': True})
    #     if duplicate_topics.count() > 1:
    #         print('%d/%d: %d' % (i, total_num, duplicate_topics.count()))
    #         print(len(topic_ids))
    #         duplicates.append(list(duplicate_topics))
    #     for duplicate_topic in duplicate_topics:
    #         topic_ids.remove(duplicate_topic['_id'])

    for i, topic in enumerate(topics):
        duplicate_topics = db.topic_collection.find({'deleted': {'$ne': True}, 'images': list(topic['images'])}, {'title': True, 'create_time': True})
        if duplicate_topics.count() > 1:
            print('%d/%d: %d' % (i, total_num, duplicate_topics.count()))
            duplicates.append(list(duplicate_topics))
    end = clock()
    print(end-begin)
    return render_template('admin/duplicate.html', duplicates=duplicates)

