"""Top-level package for xepmts."""

__author__ = """Yossi Mosbacher"""
__email__ = 'joe.mosbacher@gmail.com'
__version__ = '0.4.15'

# import eve_panel
from xepmts import api
from xepmts.api.server.v1.app import list_roles
from xepmts.api.server.v2.app import list_roles as list_v2_roles

from xepmts.api.client import default_client, get_client
from . import streams

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