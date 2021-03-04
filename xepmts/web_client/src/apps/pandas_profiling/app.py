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

from xepmts.web_client.src.shared.templates import ListTemplate
from xepmts.web_client.src.shared import config, get_db
from xepmts.web_client.src.shared._menu import session_menu
from xepmts.web_client.src.shared.models import BaseSection, DataLoader, CenterColumn
from xepmts.web_client.src.shared._session import login_required              

from pandas_profiling import ProfileReport

PARENT_DIR = pathlib.Path(__file__).parent
CONFIG_FILE = PARENT_DIR / "configuration.yaml"

class PandasProfiling(BaseSection):
    title = param.String("Collection profile")
    minimal = param.Boolean(False)
    # _report = param.Parameter(precedence=-1)
    update_report_action = param.Action(lambda self: self._update_view(), label="Create plot")

    def _init_view(self):
        self._view = pn.Column("Data not loaded yet.", sizing_mode="stretch_both")
        
    def _update_view(self, *events):
        if self.data is None:
            return
        else:
            report = ProfileReport(self.data,
                                config_file=CONFIG_FILE,
                                title=self.title)
            self._view = pn.Column(
                    pn.pane.HTML(report.to_html(), sizing_mode="stretch_both"),
                    sizing_mode="stretch_both"
                     )

    def settings(self):
        settings_parameters = ["minimal", "title", "update_report_action"]
        return pn.Param(self.param, parameters=settings_parameters)

@login_required(pn.state)                                 
def view(db):
    menu = session_menu(pn.state.curdoc.session_context.id)
    template = ListTemplate(
        title="Pandas profiling",
        sidebar_footer=menu,
    )
    pn.state.curdoc.theme = template.theme.bokeh_theme

    plotter = PandasProfiling()
    loader = DataLoader(client=db, data_plotter=plotter, _logged_in=db.logged_in)
    loader.merge_pmt_info = False
    hv.renderer('bokeh').theme = template.theme.bokeh_theme
    cards = loader.cards()
    panels = cards[:-1] + [pn.panel(plotter.view)]
    template.main[:] = panels
    template.sidebar[:] = [pn.panel(loader.settings), pn.layout.Divider()]

    return template

if __name__.startswith("bokeh"):
    view().servable()
