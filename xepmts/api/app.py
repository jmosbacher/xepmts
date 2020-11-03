import os

from xepmts.api.settings import get_settings_dict

def make_local_app():
    import eve
    settings =get_settings_dict()
    app = eve.Eve(settings=settings)
    return app
    