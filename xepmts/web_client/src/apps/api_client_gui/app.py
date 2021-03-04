import pathlib
import sqlite3 as sql
from os.path import dirname, join

import numpy as np
import pandas as pd
import panel as pn
import holoviews as hv
import param
from datetime import datetime
import time

from awesome_panel_extensions.widgets.perspective_viewer import PerspectiveViewer

from xepmts.web_client.src.shared.templates import ListTemplate
from xepmts.web_client.src.shared import config, get_db
from xepmts.web_client.src.shared._menu import session_menu
from xepmts.web_client.src.shared.models import BaseSection, DataLoader
from xepmts.web_client.src.shared._session import login_required              

@login_required(pn.state)                                 
def view(db):
    menu = session_menu(pn.state.curdoc.session_context.id)
    template = ListTemplate(
        title="Heatmap viewer",
        sidebar_footer=menu,
    )
    pn.state.curdoc.theme = template.theme.bokeh_theme

    hv.renderer('bokeh').theme = template.theme.bokeh_theme
    
    template.main[:] = [db.panel()]
    # template.sidebar[:] = [pn.panel(), pn.layout.Divider()]

    return template

if __name__.startswith("bokeh"):
    view().servable()
