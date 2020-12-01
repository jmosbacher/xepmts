# -*- coding: utf-8 -*-
import os

from .settings import get_settings_dict


def make_app(**kwargs):
    from eve import Eve
    from eve_jwt import JWTAuth
    settings = get_settings_dict()
    app = Eve(settings=settings, auth=JWTAuth, **kwargs)
    return app


def make_local_app(**kwargs):
    import eve
    settings = get_settings_dict()
    app = eve.Eve(settings=settings, **kwargs)
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