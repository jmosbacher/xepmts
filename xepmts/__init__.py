"""Top-level package for xepmts."""

__author__ = """Yossi Mosbacher"""
__email__ = 'joe.mosbacher@gmail.com'
__version__ = '0.4.12'

# import eve_panel
from xepmts import api
from xepmts.api.server.v1.app import list_roles
from xepmts.api.server.v2.app import list_roles as list_v2_roles

from xepmts.api.client import default_client, get_client


def settings(**kwargs):
    from eve_panel import settings as panel_settings
    if not kwargs:
        return dir(panel_settings)
    else:
        for k,v in kwargs.items():
            setattr(panel_settings, k, v)


def extension():
    import eve_panel
    import nest_asyncio
    eve_panel.extension()
    nest_asyncio.apply()

notebook = extension