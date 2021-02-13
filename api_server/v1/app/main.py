
import os
import xepmts
from xepmts.api.server.v1.app import make_app
from xepmts.api.server.v1.auth import XenonTokenAuth
from eve_swagger import get_swagger_blueprint
# from eve_jwt import JWTAuth
from flask_swagger_ui import get_swaggerui_blueprint
from prometheus_flask_exporter import PrometheusMetrics

def create_app():
    app = make_app(auth=XenonTokenAuth,)
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

app = create_app()


if __name__ == '__main__':
    app.run(host="localhost", debug=True, ) #ssl_context="adhoc"
    
