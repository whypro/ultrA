# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
from datetime import datetime
import os
import hashlib
from time import clock
from flask import Blueprint, request, current_app, jsonify, redirect, url_for

from ..helpers import render_template
from ..database import MongoDB


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
    db = MongoDB()
    topics = db.topics.find(
        query
    ).sort(sort).skip((page-1)*current_app.config['TOPICS_PER_ADMIN_PAGE']).limit(current_app.config['TOPICS_PER_ADMIN_PAGE'])

    count = topics.count(with_limit_and_skip=True)
    total = topics.count()

    topics = list(topics)
    for topic in topics:
        # 计算每个主题的【纯净度】
        photo_num = len(topic['photos'])
        if photo_num:
            topic['purity'] = db.photos.find({'_id': {'$in': topic['photos']}, 'blur': {'$ne': True}}).count() / photo_num
        else:
            topic['purity'] = photo_num

    pagination = dict(page=page, pages=total//current_app.config['TOPICS_PER_ADMIN_PAGE']+1)

    return topics, pagination


@admin.route('/topic/similarity/calculate/')
def calculate_similarity():
    """根据 SHA-1 计算两个主题的相似度"""
    db = MongoDB()
    for topic_A in db.topics.find({'similarity_calculated': {'$ne': True}, 'status': 'normal'}):
        photos_A = db.photos.find({'_id': {'$in': topic_A['photos']}, 'blur': {'$ne': True}})
        shas_A = [photo['sha1'] for photo in photos_A]
        for topic_B in db.topics.find({'status': 'normal', '_id': {'$ne': topic_A['_id']}}):
            photos_B = db.photos.find({'_id': {'$in': topic_B['photos']}, 'blur': {'$ne': True}})
            shas_B = [photo['sha1'] for photo in photos_B]
            # 防止被 0 除
            if not shas_A and not shas_B:
                continue
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
        db.topics.update({'_id': topic_A['_id']}, {'$set': {'similarity_calculated': True}})


@admin.route('/topic/similarity/', defaults={'page': 1})
@admin.route('/topic/similarity/<int:page>/')
def show_similar_topics(page):
    """显示相似主题"""
    db = MongoDB()
    sort = [('value', -1)]
    similarities = db.similarities.find().sort(sort).skip((page-1)*current_app.config['TOPICS_PER_ADMIN_PAGE']).limit(current_app.config['TOPICS_PER_ADMIN_PAGE'])
    total = similarities.count()
    similarities = list(similarities)
    for similarity in similarities:
        similarity['topics'] = db.topics.find({'_id': {'$in': similarity['topics']}})
    # print similarities
    pagination = dict(page=page, pages=total//current_app.config['TOPICS_PER_ADMIN_PAGE']+1)
    return render_template('admin/similarities.html', similarities=similarities, pagination=pagination)
