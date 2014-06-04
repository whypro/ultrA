# -*- coding: utf-8 -*-
from pymongo import MongoClient
from flask import current_app


class MongoDB():
    def __init__(self):
        client = MongoClient(
            host=current_app.config['DB_HOST'],
            port=current_app.config['DB_PORT'],
            tz_aware=True,
        )
        db = client[current_app.config['DB_NAME']]
        self.topic_collection = db[current_app.config['TOPIC_COLLECTION']]
        self.image_collection = db[current_app.config['IMAGE_COLLECTION']]
        self.garbage_image_collection = db[current_app.config['GARBAGE_IMAGE_COLLECTION']]

