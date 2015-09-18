# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime

from flask import Blueprint, send_from_directory, current_app, abort, redirect, send_file
from flask import url_for, request, jsonify
from bson.objectid import ObjectId

from ..helpers import render_template
from ..database import MongoDB


topic = Blueprint('topic', __name__, url_prefix='/topic_test')


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
    categories = db.topic_collection.distinct('category')
    if category and category not in categories:
        abort(404)

    condition = {'status': 'normal'}

    if category:
        condition['category'] = category

    topics = db.topic_collection.find(
        condition,
        {'title': True, 'photos': True, 'category': True, 'rating': True}
    ).sort([
        #('click_count', 1),
        ('rating', 1),
        ('_id', -1)
    ]).skip((page-1)*current_app.config['TOPICS_PER_PAGE']).limit(current_app.config['TOPICS_PER_PAGE'])

    count = topics.count(with_limit_and_skip=True)
    total = topics.count()

    topics = list(topics)
    for topic in topics:
        topic['cover_oid'] = get_cover_oid(topic)

    pagination = dict(page=page, pages=total//current_app.config['TOPICS_PER_PAGE']+1)

    print category

    return render_template('topic/topics.html', endpoint='topic.show_topics', topics=topics, category=category, pagination=pagination)


def get_cover_oid(topic):
    db = MongoDB()
    for photo_oid in topic['photos']:
        photo = db.image_collection.find_one({'_id': photo_oid, 'blur': {'$ne': True}})
        if photo:
            return str(photo['_id'])
    return None



@topic.route('/hot/', defaults={'page': 1})
@topic.route('/hot/<int:page>/')
def show_hot_topics(page):
    db = MongoDB()
    topics = db.topic_collection.find(
        {},
        {'title': True, 'photos': True, 'category': True, 'rating': True}
    ).sort([
        ('rating', -1),
        ('click_count', -1)
    ]).skip((page-1)*current_app.config['TOPICS_PER_PAGE']).limit(current_app.config['TOPICS_PER_PAGE'])

    count = topics.count(with_limit_and_skip=True)
    total = topics.count()

    topics = list(topics)
    for topic in topics:
        topic['cover_oid'] = get_cover_oid(topic)

    pagination = dict(page=page, pages=total//current_app.config['TOPICS_PER_PAGE']+1)

    return render_template('topic/topics.html', endpoint='topic.show_hot_topics', topics=topics, pagination=pagination)


@topic.route('/<oid>/')
def show_topic_detail(oid):
    db = MongoDB()
    topic_ = db.topic_collection.find_one({'_id': ObjectId(oid)})
    if not topic_:
        abort(404)

    # rating = topic.get('rating')

    # 按顺序查找图片
    photos = []
    for photo_oid in topic_['photos']:
        photo = db.image_collection.find_one({'_id': photo_oid, 'blur': {'$ne': True}})
        if photo:
            photos.append(photo)

    print len(photos)

    # 点击量 +1
    db.topic_collection.update({'_id': ObjectId(oid)}, {'$inc': {'click_count': 1}})

    return render_template('topic/topic_detail.html', topic=topic_, photos=photos)


@topic.route('/<oid>/_edit/', methods=['POST'])
def ajax_edit_topic(oid):
    title = request.form.get('title')
    rating = request.form.get('rating')

    if rating not in (None, '1', '2', '3', '4', '5'):
        abort(400)

    db = MongoDB()

    set_data = {'modify_time': datetime.utcnow()}
    if title:
        set_data['title'] = title
    if rating:
        set_data['rating'] = int(rating)

    db.topic_collection.update({'_id': ObjectId(oid)}, {'$set': set_data})
    # topic = db.topic_collection.find_one({'_id': ObjectId(oid)}, {'title': True, 'rating': True})
    return jsonify(set_data, success=True)
