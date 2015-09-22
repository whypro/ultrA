# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flask import Flask, g, flash, redirect, url_for
from flask.ext.themes import setup_themes
from pymongo import MongoClient
from ultrA import views
from ultrA.database import MongoDB


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config)
    config_blueprints(app)
    config_error_handlers(app)
    configure_theme(app)
    config_context_processor(app)

    return app


def config_blueprints(app):
    app.register_blueprint(views.home)
    app.register_blueprint(views.topic)
    app.register_blueprint(views.photo)
    app.register_blueprint(views.admin)


def configure_theme(app):
    setup_themes(app)


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
        db = MongoDB()
        categories = db.topics.distinct('category')
        return dict(categories=categories)
