# -*- coding: utf-8 -*-
from pymongo import MongoClient
from flask import current_app


class UltrADB(object):
    def __init__(self, app=None):
        self.app = app
        if app: 
            self.init_app(app)

    def init_app(self, app):
        # 连接数据库
        client = MongoClient(
            host=app.config['DB_HOST'],
            port=app.config['DB_PORT'],
            tz_aware=True,
        )
        db = client[app.config['DB_NAME']]
        self.topics = db[app.config['TOPIC_COLLECTION']]
        self.photos = db[app.config['PHOTO_COLLECTION']]
        self.blurs = db[app.config['BLUR_COLLECTION']]
        self.similarities = db['raw_similarities']
        self.sites = db['raw_sites']


db = UltrADB()
