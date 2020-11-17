"""Top-level package for xepmts."""

__author__ = """Yossi Mosbacher"""
__email__ = 'joe.mosbacher@gmail.com'
__version__ = '0.4.5'

from .api.app import list_roles
from . import api

def settings(**kwargs):
    from eve_panel import settings as panel_settings
    if not kwargs:
        return dir(panel_settings)
    else:
        for k,v in kwargs.items():
            setattr(panel_settings, k, v)

def default_client():
    from xepmts.api.client import default_client
    return default_client()

def extension():
    import eve_panel
    eve_panel.extension()

notebook = extension