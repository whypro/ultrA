# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
from datetime import datetime

from flask import Blueprint, send_from_directory, current_app, abort
from flask import url_for, request, jsonify
from bson.objectid import ObjectId

from ..helpers import render_template
from ..database import MongoDB


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
    db = MongoDB()
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
    db = MongoDB()
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
    db = MongoDB()
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
    db = MongoDB()
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
    topic['purity'] = len(photos) / len(topic['photos'])

    # 点击量 +1
    db.topics.update({'_id': ObjectId(oid)}, {'$inc': {'click_count': 1}})

    return render_template('topic/topic_detail.html', topic=topic, photos=photos)


@topic.route('/<oid>/_title/', methods=['POST'])
def ajax_edit_title(oid):
    title = request.form.get('title')

    if not title:
        abort(400)

    db = MongoDB()
    db.topics.update({'_id': ObjectId(oid)}, {'$set': {'title': title}})

    return jsonify(success=True)


@topic.route('/<oid>/_rating/', methods=['POST'])
def ajax_edit_rating(oid):
    rating = request.form.get('rating')
    if rating not in ('0', '1', '2', '3', '4', '5'):
        abort(400)

    rating = int(rating)
    db = MongoDB()

    if rating:
        db.topics.update({'_id': ObjectId(oid)}, {'$set': {'modify_time': datetime.utcnow(), 'rating': rating}})
    else:
        db.topics.update({'_id': ObjectId(oid)}, {'$unset': {'modify_time': datetime.utcnow(), 'rating': ''}})

    return jsonify(success=True)
