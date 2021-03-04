import os
import xepmts

from flask import Flask


from threading import Lock
from werkzeug.wsgi import pop_path_info, peek_path_info
from werkzeug.serving import run_simple as _run_simple

from xepmts.api.server.v1.app import make_app as make_v1_app
from xepmts.api.server.v1.auth import XenonTokenAuth
from xepmts.api.server.v2.app import make_app as make_v2_app
from xepmts.api.server.utils import PathDispatcher

def create_app():
    from eve_jwt import JWTAuth
    from flask_swagger_ui import get_swaggerui_blueprint
    from prometheus_flask_exporter import PrometheusMetrics

    v1 = make_v1_app(auth=XenonTokenAuth, swagger=True)
    v2 = make_v2_app(auth=JWTAuth, swagger=True)
    app_versions = {
        "v1": v1, 
        "v2": v2
        }
    app = Flask(__name__)
    # @app.route("/")
    # def hello():
    #     return "You have reached the PMT db."

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
    # PrometheusMetrics(app)

    application = PathDispatcher(app,
                         app_versions)

    return application

def run_simple(address='0.0.0.0', port=5000, debug=True, reload=True, evalex=True):
    app = create_app()
    _run_simple(address, port, app,
                use_reloader=debug, use_debugger=reload, use_evalex=evalex)

if __name__ == '__main__':
    run_simple()
    

