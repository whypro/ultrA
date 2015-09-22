# -*- coding: utf-8 -*-
from pymongo import MongoClient
from flask import current_app


class MongoDB(object):
    def __init__(self):
        self.__client = MongoClient(
            host=current_app.config['DB_HOST'],
            port=current_app.config['DB_PORT'],
            tz_aware=True,
        )
        db = self.__client[current_app.config['DB_NAME']]
        self.topics = db[current_app.config['TOPIC_COLLECTION']]
        self.photos = db[current_app.config['PHOTO_COLLECTION']]
        self.blurs = db[current_app.config['BLUR_COLLECTION']]
        self.similarities = db['raw_similarities']

    def __del__(self):
        self.__client.close()
