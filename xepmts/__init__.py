"""Top-level package for xepmts."""

__author__ = """Yossi Mosbacher"""
__email__ = 'joe.mosbacher@gmail.com'
__version__ = '0.5.3'

import xeauth
from xepmts.db.client import default_client, get_client, get_admin_client
from . import streams
from .settings import config

def login(version,
          username=None,
          password=None,
          token=None, 
          scopes=["openid profile email offline_access read:all"],
          auth_kwargs={},
          **kwargs):
    auth_kwargs = dict(auth_kwargs)
    scope = " ".join(scopes)
    audience = auth_kwargs.pop('audience', config.OAUTH_AUDIENCE)

    if token is not None:
        xetoken = xeauth.tokens.XeToken(access_token=token)
    elif username is not None:
        xetoken = xeauth.user_login(username=username, password=password, scope=scope, audience=audience, **auth_kwargs )
    else:
        xetoken = xeauth.login(scopes=scope, audience=audience, **auth_kwargs)
    return get_client(version, xetoken=xetoken, **kwargs)

def settings(**kwargs):
    from eve_panel import settings as panel_settings
    if not kwargs:
        return dir(panel_settings)
    else:
        for k,v in kwargs.items():
            setattr(panel_settings, k, v)

def extension():
    import eve_panel
    eve_panel.extension()

notebook = extension