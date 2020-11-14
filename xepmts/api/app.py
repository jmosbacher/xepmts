# -*- coding: utf-8 -*-
import os

from xepmts.api.settings import get_settings_dict


def make_app(settings=None, auth=None, app=None,
             swagger=True, swagger_ui=True, fs_store=False,
             export_metrics=True):
    if app is None and settings is None:
        settings = get_settings_dict()
        raise RuntimeError("App or settings need to be defined.")
    kwargs = {}
    if fs_store:
        from eve_fsmediastorage import FileSystemMediaStorage
        kwargs["media"] = FileSystemMediaStorage
    if app is None:
        from eve import Eve
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
    if export_metrics:
        from prometheus_flask_exporter import PrometheusMetrics
        PrometheusMetrics(app)
    return app


def make_local_app():
    import eve
    settings = get_settings_dict()
    app = eve.Eve(settings=settings)
    return app
    
def list_roles():
    settings = get_settings_dict()
    roles = set()
    for resource in settings["DOMAIN"].values():
        roles.update(resource["allowed_read_roles"])
        roles.update(resource["allowed_item_read_roles"])
        roles.update(resource["allowed_write_roles"])
        roles.update(resource["allowed_item_write_roles"])
    roles = list(roles)
    roles.sort(key=lambda x: x.split(":")[-1])
    return roles