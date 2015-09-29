# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import Flask, g, flash, redirect, url_for
from pymongo import MongoClient

from . import views
from .database import db
from .deps.flaskext.themes import setup_themes


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config)
    config_blueprints(app)
    config_error_handlers(app)
    configure_theme(app)
    config_context_processor(app)

    db.init_app(app)

    init_site_name(app)

    return app


def config_blueprints(app):
    app.register_blueprint(views.home)
    app.register_blueprint(views.topic)
    app.register_blueprint(views.photo)
    app.register_blueprint(views.admin)


def configure_theme(app):
    setup_themes(app)

def init_site_name(app):
    site = db.sites.find_one({'avaliable': True})
    if site:
        # print site['name']
        app.config['ORIGIN_SITE'] = site['name']

def config_error_handlers(app):
    pass
    # @app.errorhandler(404)
    # def page_not_found(e):
    #     print('404')
    #     flash('页面未找到', 'danger')
    #     return redirect(url_for('frontend.index'))
    #
    # @app.errorhandler(401)
    # def unauthorized(e):
    #     flash('未经授权', 'danger')
    #     return redirect(url_for('frontend.index'))
    #
    # @app.errorhandler(500)
    # def internal_server_error(e):
    #     flash('服务器开小差了', 'danger')
    #     return redirect(url_for('frontend.index'))


def config_context_processor(app):
    @app.context_processor
    def inject_categories():
        categories = db.topics.distinct('category')
        return dict(categories=categories)
