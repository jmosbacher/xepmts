
import param
import panel as pn
import holoviews as hv
import numpy as np
import base64
import pandas as pd
from pandas.api.types import is_numeric_dtype
import streamz
from streamz.dataframe import PeriodicDataFrame
import httpx
import hvplot
import os

from xepmts.web_client.src.shared.templates import ListTemplate
from xepmts.web_client.src.shared import config, get_db
from xepmts.web_client.src.shared._menu import session_menu
from xepmts.web_client.src.shared._session import login_required
from xepmts.web_client.src.shared.models import BaseSection, FilterTool, CenterColumn
from xepmts.streams import get_live_rate_viewer

class RatesViewer(param.Parameterized):
    client = param.Parameter()
    api_user = param.String()
    api_key = param.String()
    stream_viewer = param.Parameter()
    detectors = param.ListSelector(default=["tpc", "nveto", "muveto"],
     objects=["tpc", "nveto", "muveto"])
    get_viewer_button = param.Action(lambda self: self.get_viewer(), label="Generate viewer")
    loading = param.Boolean(False)

    def get_viewer(self):
        self.loading = True
        try:
            self.stream_viewer = get_live_rate_viewer(db=self.client,
                                                  api_user=self.api_user, 
                                                  api_key=self.api_key,
                                                  detectors=self.detectors)
        finally:
            self.loading = False

    def credentials_view(self):
        return pn.Column(self.param.api_user,
                         self.param.api_key)

    @param.depends("stream_viewer", "loading")
    def view(self):
        if self.loading:
            return CenterColumn(pn.indicators.LoadingSpinner(value=True))

        if self.stream_viewer is None:
            return self.settings()
        else:
            return self.stream_viewer.view()

    def settings(self):
        return pn.Column(self.credentials_view(),
                    self.param.detectors,
                    self.param.get_viewer_button,
                            )

    @property
    def sections(self):
        return {"Live DAQ streams": self.view}
    

@login_required(pn.state)          
def view(db):
    # db = pn.state.as_cached(pn.state.curdoc.session_context.id, get_db)
    menu = session_menu(pn.state.curdoc.session_context.id)
    template = ListTemplate(
        title="Live data rates",
        sidebar_footer=menu,
    )
    pn.state.curdoc.theme = template.theme.bokeh_theme
    api_user = os.getenv("DAQ_API_USER", "")
    api_key = os.getenv("DAQ_API_KEY", "")

    browser = RatesViewer(client=db, api_user=api_user, api_key=api_key)

    hv.renderer('bokeh').theme = template.theme.bokeh_theme
    template.main[:] = [CenterColumn("## "+k, v ,sizing_mode="stretch_both") for k,v in browser.sections.items()]
    template.sidebar[:] = [pn.panel(browser.settings)]
    return template


if __name__.startswith("bokeh"):
    view().servable()
