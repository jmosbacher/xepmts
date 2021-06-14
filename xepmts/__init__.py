"""Top-level package for xepmts."""

__author__ = """Yossi Mosbacher"""
__email__ = 'joe.mosbacher@gmail.com'
__version__ = '0.4.25'

from xepmts.db.client import default_client, get_client
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