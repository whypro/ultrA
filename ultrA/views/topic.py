# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
import datetime
import os
import shutil

from flask import Blueprint, send_from_directory, current_app, abort
from flask import url_for, request, jsonify
from bson.objectid import ObjectId

from ..helpers import render_template
from ..database import db


topic = Blueprint('topic', __name__, url_prefix='/topic')


@topic.route('/', defaults={'page': 1})
@topic.route('/<int:page>/')
@topic.route('/category/<category>/', defaults={'page': 1})
@topic.route('/category/<category>/<int:page>/')
def show_topics(page, category=None):
    """Topics page.

    show topics.

    Args:
        category: filter by category, if category == None, then return all topics

    Returns:
        topics: a list of topics
        category: same to the arg category
    """
    categories = db.topics.distinct('category')
    if category and category not in categories:
        abort(404)

    query = dict()
    query['status'] = 'normal'

    if category:
        query['category'] = category

    sort = [('rating', 1), ('_id', -1)]

    topics, pagination = load_topics(query=query, sort=sort, page=page)

    return render_template('topic/topics.html', endpoint='topic.show_topics', args={'category': category}, topics=topics, pagination=pagination)


def load_topics(query, sort, page):
    topics = db.topics.find(
        query,
        {'title': True, 'photos': True, 'category': True, 'rating': True}
    ).sort(sort).skip((page-1)*current_app.config['TOPICS_PER_PAGE']).limit(current_app.config['TOPICS_PER_PAGE'])

    count = topics.count(with_limit_and_skip=True)
    total = topics.count()

    topics = list(topics)
    for topic in topics:
        topic['cover_oid'] = get_cover_oid(topic)

    pagination = dict(page=page, pages=total//current_app.config['TOPICS_PER_PAGE']+1)

    return topics, pagination


def get_cover_oid(topic):
    for photo_oid in topic['photos']:
        photo = db.photos.find_one({'_id': photo_oid, 'blur': {'$ne': True}})
        if photo:
            return str(photo['_id'])
    return None



@topic.route('/hot/', defaults={'page': 1})
@topic.route('/hot/<int:page>/')
def show_hot_topics(page):
    query = {'status': 'normal'}
    sort = [('rating', -1), ('click_count', -1)]
    topics, pagination = load_topics(query=query, sort=sort, page=page)

    return render_template('topic/topics.html', endpoint='topic.show_hot_topics', args={}, topics=topics, pagination=pagination)


@topic.route('/search/<key>/', defaults={'page': 1})
@topic.route('/search/<key>/<int:page>/')
def show_match_topic(key, page):
    print(key)
    query = dict()
    query['status'] = 'normal'
    query['title'] = {'$regex': key, '$options': '$i'}
    sort = [('rating', -1), ('_id', -1)]
    topics, pagination = load_topics(query=query, sort=sort, page=page)

    return render_template('topic/topics.html', endpoint='topic.show_match_topic', args={'key': key}, topics=topics, pagination=pagination)


@topic.route('/<oid>/')
def show_topic_detail(oid):
    topic = db.topics.find_one({'_id': ObjectId(oid)})
    if not topic:
        abort(404)

    # 按顺序查找图片
    photos = []
    for photo_oid in topic['photos']:
        photo = db.photos.find_one({'_id': photo_oid, 'blur': {'$ne': True}})
        if photo:
            photos.append(photo)

    # 计算纯净度
    topic['purity'] = len(photos) / len(topic['photos']) if topic['photos'] else 0

    # 点击量 +1
    db.topics.update({'_id': ObjectId(oid)}, {'$inc': {'click_count': 1}})

    return render_template('topic/topic_detail.html', topic=topic, photos=photos)


@topic.route('/<oid>/_title/', methods=['POST'])
def ajax_edit_title(oid):
    title = request.form.get('title')

    if not title:
        abort(400)

    db.topics.update({'_id': ObjectId(oid)}, {'$set': {'title': title, 'modify_time': datetime.datetime.utcnow()}})

    return jsonify(success=True)


@topic.route('/<oid>/_rating/', methods=['POST'])
def ajax_edit_rating(oid):
    rating = request.form.get('rating')
    if rating not in ('0', '1', '2', '3', '4', '5'):
        abort(400)

    rating = int(rating)

    # 查找相同的主题
    similarities = db.similarities.find({'topics': ObjectId(oid), 'value': 1}, {'topics': True})
    same = set()
    for s in similarities:
        same |= set(s['topics'])
    same = list(same)
    # print same

    if rating:
        db.topics.update({'_id': {'$in': same}}, {'$set': {'rating': rating, 'modify_time': datetime.datetime.utcnow()}}, multi=True)
    else:
        db.topics.update({'_id': {'$in': same}}, {'$set': {'modify_time': datetime.datetime.utcnow()}, '$unset': {'rating': ''}}, multi=True)

    return jsonify(success=True)


@topic.route('/<oid>/_delete/', methods=['POST'])
def ajax_delete(oid):
    delete_type = request.form.get('delete_type')
    if delete_type not in ('delete', 'remove', 'wipe'):
        abort(400)

    if delete_type == 'delete':
        # 仅标记为已删除
        db.topics.update({'_id': ObjectId(oid)}, {'$set': {'status': 'deleted', 'modify_time': datetime.datetime.utcnow()}})
        print 'delete'
    elif delete_type == 'remove':
        # 删除/数据库记录
        remove_topic_dir(oid)
        db.photos.remove({'topic': ObjectId(oid)})
        db.topics.update({'_id': ObjectId(oid)}, {'$set': {'photos': [], 'status': 'removed', 'modify_time': datetime.datetime.utcnow()}})
        print 'remove'
    elif delete_type == 'wipe':
        # 删除对应目录
        remove_topic_dir(oid)
        # 删除数据库记录
        db.photos.remove({'topic': ObjectId(oid)})
        db.topics.remove({'_id': ObjectId(oid)})
        print 'wipe'

    return jsonify(status=200)

def remove_topic_dir(oid):
    # 删除对应目录
    topic_path = None
    topic = db.topics.find_one({'_id': ObjectId(oid)}, {'path': True})
    if topic:
        if 'path' in topic:
            # 首先从 topics 集合中找 path
            topic_path = os.path.join(current_app.config['MEDIA_PATH'], topic['path'])
        else:
            # 其次从 photos 集合中生成 path
            first_photo = db.photos.find_one({'topic': ObjectId(oid)})
            if first_photo:
                topic_path = os.path.dirname(os.path.join(current_app.config['MEDIA_PATH'], first_photo['path']))

    if topic_path and os.path.exists(topic_path):
        print topic_path
        shutil.rmtree(topic_path)
