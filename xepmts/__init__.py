"""Top-level package for xepmts."""

__author__ = """Yossi Mosbacher"""
__email__ = 'joe.mosbacher@gmail.com'
__version__ = '__version__ = '0.1.1''

import os

import panel as pn
from eve_panel import settings as panel_settings

from xepmts.api.client import default_client

def notebook():
    return pn.extension()

