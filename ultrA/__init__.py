# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from flask import Flask, g, flash, redirect, url_for
from flask.ext.themes import setup_themes
from ultrA import views


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config)

    config_blueprints(app)
    config_error_handlers(app)
    configure_theme(app)

    return app


def config_blueprints(app):
    app.register_blueprint(views.frontend)


def configure_theme(app):
    setup_themes(app)


def config_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        flash('页面未找到', 'danger')
        return redirect(url_for('frontend.index'))

    @app.errorhandler(401)
    def unauthorized(e):
        flash('未经授权', 'danger')
        return redirect(url_for('frontend.index'))

    @app.errorhandler(500)
    def internal_server_error(e):
        flash('服务器开小差了', 'danger')
        return redirect(url_for('frontend.index'))
