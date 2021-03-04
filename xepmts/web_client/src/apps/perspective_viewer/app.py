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

settings_parameters = [
        "theme",
        "row_pivots",
        "plugin",
        "columns",
        "aggregates",
        "filters",
        "sort",
        "rows",
        "column_pivots",
    ]

class PerspectivePlotter(BaseSection):

    _plot = param.Parameter(precedence=-1)
    update_plot_action = param.Action(lambda self: self.update_plot(), label="Create plot")

    def _init_view(self):
        self._view = pn.Column("Data not loaded yet.", sizing_mode="stretch_both")
        
    def _update_view(self, *events):
        if self.data is None:
            self.update_plot_action.disabled = True
        else:
            self._plot = PerspectiveViewer(
            value=self.data, columns=list(self.data), 
            height=900,
            theme="material-dark", sizing_mode="stretch_width"
        )
            
    @param.depends("loading", "data", "_plot")
    def view(self):
        if self.data is None or not len(self.data):
            return pn.Column("# No data to show.")
        if self._plot is None:
            button = pn.widgets.Button(name="Build viewer", button_type="primary")
            return pn.Param(self.param.update_plot_action, widgets={"update_plot_action": button})
        else:
            return self._plot

    def update_plot(self):
        pass

    def settings(self):
        if self._plot is None:
            return pn.Column()
        else:
            return pn.Param(self._plot.param, parameters=settings_parameters)

@login_required(pn.state)                                 
def view(db):
    menu = session_menu(pn.state.curdoc.session_context.id)
    template = ListTemplate(
        title="Heatmap viewer",
        sidebar_footer=menu,
    )
    pn.state.curdoc.theme = template.theme.bokeh_theme

    plotter = PerspectivePlotter()
    loader = DataLoader(client=db, data_plotter=plotter, _logged_in=db.logged_in)

    hv.renderer('bokeh').theme = template.theme.bokeh_theme
    
    template.main[:] = [pn.panel(c) for c in loader.cards()]
    template.sidebar[:] = [pn.panel(loader.settings), pn.layout.Divider()]

    return template

if __name__.startswith("bokeh"):
    view().servable()
