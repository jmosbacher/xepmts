# -*- coding: utf-8 -*-

from eve import Eve
from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
from prometheus_flask_exporter import PrometheusMetrics
import os


def make_app(settings, auth, swagger=True, swagger_ui=True, fs_store=False):
    kwargs = {}
    if fs_store:
        from eve_fsmediastorage import FileSystemMediaStorage
        kwargs["media"] = FileSystemMediaStorage

    app = Eve(settings=settings, auth=auth, **kwargs)

    if swagger:
        # from eve_swagger import swagger as swagger_blueprint
        from eve_swagger import get_swagger_blueprint
        
        swagger_blueprint = get_swagger_blueprint()
        app.register_blueprint(swagger_blueprint)
        app.config['SWAGGER_INFO'] = {
            'title': 'XENON PMT API',
            'version': '1.0',
            'description': 'API for the XENON PMT database',
            'termsOfService': 'https://opensource.org/ToS',
            'contact': {
                'name': 'Yossi Mosbacher',
                'url': 'https://pmts.xenonnt.org',
                "email": "joe.mosbacher@gmail.com"
            },

            'license': {
                'name': 'BSD',
                'url': 'https://github.com/nicolaiarocci/eve-swagger/blob/master/LICENSE',
            
            },
            'schemes': ['http', 'https'],

        }

    if swagger_ui:
        from flask_swagger_ui import get_swaggerui_blueprint

        API_URL = '/api-docs'
        SWAGGER_URL = ''
        SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
            SWAGGER_URL,
            API_URL,
            config={
                'app_name': "PMT Database API"
            },
        )
        app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
    PrometheusMetrics(app)
    return app

def make_local_app():
    from xepmts.api.app.settings import SETTINGS_DIR
    SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.py")
    app = make_app(SETTINGS_FILE, auth=None, swagger=True, swagger_ui=True)
    return app
    
if __name__ == '__main__':
    app = make_local_app()
    app.run(host="localhost", debug=True, ) #ssl_context="adhoc"
    
    # from werkzeug.middleware.dispatcher import DispatcherMiddleware
    # application = DispatcherMiddleware(app, {
    #     '/api': app
    # })
    # from werkzeug.serving import run_simple
    # run_simple('localhost', 5000, application, use_reloader=True)