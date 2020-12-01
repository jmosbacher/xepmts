"""Top-level package for xepmts."""

__author__ = """Yossi Mosbacher"""
__email__ = 'joe.mosbacher@gmail.com'
__version__ = '0.4.6'

# import eve_panel
from . import api
from .api.app import list_roles

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