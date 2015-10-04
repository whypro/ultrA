# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
import datetime
import os
import hashlib
from time import clock
from flask import Blueprint, request, current_app, jsonify, redirect, url_for

from ..helpers import render_template
from ..database import db
from .topic import delete_topic


admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.route('/')
def index():
    return render_template('admin/index.html')


@admin.route('/topic/', defaults={'page': 1})
@admin.route('/topic/<int:page>/')
def show_topics(page):

    query = request.args.to_dict()
    sort = [('_id', -1)]
    print query

    topics, pagination = load_topics(query=query, sort=sort, page=page)
    return render_template('admin/topics.html', topics=topics, pagination=pagination)


def load_topics(query, sort, page):
    topics = db.topics.find(
        query
    ).sort(sort).skip((page-1)*current_app.config['TOPICS_PER_ADMIN_PAGE']).limit(current_app.config['TOPICS_PER_ADMIN_PAGE'])

    count = topics.count(with_limit_and_skip=True)
    total = topics.count()

    topics = list(topics)
    # for topic in topics:
    #     pass

    pagination = dict(page=page, pages=total//current_app.config['TOPICS_PER_ADMIN_PAGE']+1)

    return topics, pagination


@admin.route('/topic/purity/calculate/')
def calculate_purity():
    """计算主题的纯净度"""
    for topic in db.topics.find({'purity_calculated': {'$ne': True}, 'status': 'normal'}):
        photo_num = db.photos.find({'topic': topic['_id'], 'blur': {'$ne': True}}).count()
        topic['purity'] = photo_num / len(topic['photos']) if topic['photos'] else 0
        topic['modify_time'] = datetime.datetime.utcnow()
        topic['purity_calculated'] = True
        db.topics.save(topic)

    # 删除纯净度为 0 的主题
    for topic in db.topics.find({'purity': 0, 'status': 'normal'}, {'_id': True}):
        delete_topic(topic['_id'], 'remove')

    return jsonify(status=200)


@admin.route('/topic/similarity/calculate/2/')
def calculate_similarity_2():
    """根据 SHA-1 计算两个主题的相似度"""
    topic_A_cursor = db.topics.find({'similarity_calculated': {'$ne': True}, 'status': 'normal'}, {'_id': True}, timeout=False)
    count = topic_A_cursor.count()
    for i, topic_A in enumerate(topic_A_cursor):
        print 'similarity_calculating:', i, '/', count
        photos_A = db.photos.find({'topic': topic_A['_id'], 'blur': {'$ne': True}})
        # photos_A = db.photos.find({'_id': {'$in': topic_A['photos']}, 'blur': {'$ne': True}})
        shas_A = [photo['sha1'] for photo in photos_A]
        for topic_B in db.topics.find({'status': 'normal', '_id': {'$ne': topic_A['_id']}}, {'_id': True}):
            photos_B = db.photos.find({'topic': topic_B['_id'], 'blur': {'$ne': True}})
            if not len(shas_A) or not photos_B.count():
                similarity_value = 0
            else:
                # photos_B = db.photos.find({'_id': {'$in': topic_B['photos']}, 'blur': {'$ne': True}})
                shas_B = [photo['sha1'] for photo in photos_B]
                # 防止被 0 除
                similarity_value = 2 * len(set(shas_A) & set(shas_B)) / (len(shas_A) + len(shas_B))

            if similarity_value > 0:
                print similarity_value
                print topic_A['_id'], topic_B['_id']
                # 更新或插入相似度
                similarity_record = db.similarities.find_one({'topics': {'$all': [topic_A['_id'], topic_B['_id']]}})
                if similarity_record:
                    db.similarities.update({'_id': similarity_record['_id']}, {'$set': {'value': similarity_value}})
                else:
                    db.similarities.insert({'topics': [topic_A['_id'], topic_B['_id']], 'value': similarity_value})
            else:
                # 可能是重新计算后 = 0，因此需要删除
                # print 'remove similarity...'
                # if db.similarities.find({'topics': {'$all': [topic_A['_id'], topic_B['_id']]}}).count():
                db.similarities.remove({'topics': {'$all': [topic_A['_id'], topic_B['_id']]}}, multi=False)

        db.topics.update({'_id': topic_A['_id']}, {'$set': {'similarity_calculated': True, 'modify_time': datetime.datetime.utcnow()}})
    topic_A_cursor.close()
    return jsonify(status=200)


@admin.route('/topic/similarity/calculate/')
def calculate_similarity():
    """根据 SHA-1 计算两个主题的相似度"""
    topics = []
    for topic in db.topics.find({'status': 'normal'}, {'photos': True, 'similarity_calculated': True}):
        photos = db.photos.find({'topic': topic['_id'], 'blur': {'$ne': True}}, {'sha1': True})
        topic['photos'] = [photo['sha1'] for photo in photos]
        topics.append(topic)

    i = 0
    for topic_A in topics:
        if topic_A.get('similarity_calculated'):
            # 已经计算过了
            continue
        print 'calculating...', i
        for topic_B in topics:
            if topic_B == topic_A:
                continue
            shas_A, shas_B = topic_A['photos'], topic_B['photos']
            # 开始计算
            if not len(shas_A) or not len(shas_B):
                similarity_value = 0
            else:
                similarity_value = 2 * len(set(shas_A) & set(shas_B)) / (len(shas_A) + len(shas_B))

            if similarity_value > 0:
                print similarity_value
                print topic_A['_id'], topic_B['_id']
                # 更新或插入相似度
                # db.similarities.update({'topics': {'$all': [topic_A['_id'], topic_B['_id']]}}, {'$set': {'value': similarity_value}}, upsert=True)
                similarity_record = db.similarities.find_one({'topics': {'$all': [topic_A['_id'], topic_B['_id']]}})
                if similarity_record:
                    db.similarities.update({'_id': similarity_record['_id']}, {'$set': {'value': similarity_value}})
                else:
                    db.similarities.insert({'topics': [topic_A['_id'], topic_B['_id']], 'value': similarity_value})
            else:
                # 可能是重新计算后 = 0，因此需要删除
                # print 'remove similarity...'
                # if db.similarities.find({'topics': {'$all': [topic_A['_id'], topic_B['_id']]}}).count():
                # db.similarities.update({'topics': {'$all': [topic_A['_id'], topic_B['_id']]}}, {'$set': {'value': similarity_value}})
                db.similarities.remove({'topics': {'$all': [topic_A['_id'], topic_B['_id']]}})

        db.topics.update({'_id': topic_A['_id']}, {'$set': {'similarity_calculated': True, 'modify_time': datetime.datetime.utcnow()}})
        i += 1
    return jsonify(status=200)


@admin.route('/topic/similarity/', defaults={'page': 1})
@admin.route('/topic/similarity/<int:page>/')
def show_similar_topics(page):
    """显示相似主题"""
    sort = [('value', -1)]
    similarities = db.similarities.find().sort(sort).skip((page-1)*current_app.config['TOPICS_PER_ADMIN_PAGE']).limit(current_app.config['TOPICS_PER_ADMIN_PAGE'])
    total = similarities.count()
    similarities = list(similarities)
    for similarity in similarities:
        similarity['topics'] = db.topics.find({'_id': {'$in': similarity['topics']}})
    # print similarities
    pagination = dict(page=page, pages=total//current_app.config['TOPICS_PER_ADMIN_PAGE']+1)
    return render_template('admin/similarities.html', similarities=similarities, pagination=pagination)
