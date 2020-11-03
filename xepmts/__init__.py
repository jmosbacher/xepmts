"""Top-level package for xepmts."""

__author__ = """Yossi Mosbacher"""
__email__ = 'joe.mosbacher@gmail.com'
__version__ = '0.1.1'

import os

from .api_client import make_client

import panel as pn
from eve_panel import settings as panel_settings

def notebook():
    return pn.extension()

# SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.py")
def get_client(name=None):
    # client = make_client(SETTINGS_FILE)
    client = make_client(name)
    return client