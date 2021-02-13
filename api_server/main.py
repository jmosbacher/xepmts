
import os
import xepmts

from flask import Flask
from eve_swagger import get_swagger_blueprint

from flask_swagger_ui import get_swaggerui_blueprint
from prometheus_flask_exporter import PrometheusMetrics

from threading import Lock
from werkzeug.wsgi import pop_path_info, peek_path_info
from werkzeug.serving import run_simple

from xepmts.api.server.v1.app import make_app as make_v1_app
from xepmts.api.server.v1.auth import XenonTokenAuth

from xepmts.api.server.v2.app import make_app as make_v2_app
from eve_jwt import JWTAuth


class PathDispatcher:

    def __init__(self, base_app, app_dict):
        self.base_app = base_app
        self.apps = app_dict

    def __call__(self, environ, start_response):
        app = self.apps.get(peek_path_info(environ), self.base_app)
        return app(environ, start_response)

def create_app():
    v1 = make_v1_app(auth=XenonTokenAuth)
    v2 = make_v2_app(auth=JWTAuth,)
    app_versions = {
        "v1": v1, 
        "v2":v2
        }
    app = Flask(__name__)
    
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
    config = {
        'app_name': "PMT Database API",
        "urls": [{"name": f"Xenon PMT Database {v.capitalize()}", "url": f"/{v}/api-docs" } for v in app_versions]
    }
    API_URL = '/v2/api-docs'
    SWAGGER_URL = ''
    SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config=config,
    )
    app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
    PrometheusMetrics(app)

    application = PathDispatcher(app,
                         app_versions)

    return application

app = create_app()


if __name__ == '__main__':

    run_simple('localhost', 5000, app,
               use_reloader=True, use_debugger=True, use_evalex=True)

