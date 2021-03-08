
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

from xepmts.web_client.src.shared.templates import ListTemplate
from xepmts.web_client.src.shared import config, get_db
from xepmts.web_client.src.shared._menu import session_menu
from xepmts.web_client.src.shared._session import login_required
from xepmts.web_client.src.shared.models import BaseSection, FilterTool, CenterColumn

READERS = {
    "tpc": [f"reader{i}_reader_0" for i in range(4)],
    "nveto": ["reader6_reader_0"],
}

MERGE_ON  = {
    "tpc": "pmt_index",
    "nveto": "signal_channel",
    
}
BACKLOG={
    "tpc":494,
    "nveto": 120, 
}

DETECTOR_DEFAULTS = {
    "tpc": {
        "xaxis": "position_x", 
        "yaxis": "position_y",
        "groupby":"array",
        },

    "nveto": {
        "xaxis": "sector", 
        "yaxis": "array",
        "groupby":"detector",
    }
}

class RatesViewer(param.Parameterized):
    client = param.Parameter()
    detector = param.Selector(list(READERS), default="nveto")
    stream = param.Parameter()
    api_user = param.String()
    api_key = param.String()
    installs = param.DataFrame()
    interval = param.Number(default=1, bounds=(1, None))
    loading = param.Boolean(False)
    xaxis = param.Selector(["position_x", "sector"], default="sector")
    yaxis = param.Selector(["position_y", "array"], default="array")
    groupby = param.Selector(["array", "detector"], default="detector")
    ncols = param.Integer(2)
    
    _plot = param.Parameter()
    running_detector = param.Selector(list(READERS))
    
    start_button = param.Action(lambda self: self.update_plot(), label="Start")
    def get_callback(self, readers, merge_on, installs):
#         readers = READERS[self.detector]
#         installs = self.installs.copy()
#         merge_on = MERGE_ON[self.detector]
        
        def callback(readers=readers, merge_on=merge_on, installs=installs, **kwargs):
  
            rates = []
            for name in readers:
                try:
                    r = httpx.get(f"https://xenonnt.lngs.infn.it/api/getstatus/{name}", 
                              params={'api_user': self.api_user, 'api_key': self.api_key})
                    channels = r.json()[0]['channels']
                    df = pd.DataFrame(channels.items(), columns=[merge_on, "rate"])
                    df[merge_on] = df[merge_on].astype(int)
                    rates.append(df)
                except:
                    pass
            if len(rates)==1:
                rates = rates[0]
            elif len(rates)>1:
                rates = pd.concat(rates)
            else:
                rates = installs[merge_on].copy()
                rates["rate"] = np.nan
            return installs.merge(rates)
        return callback
    
    def init_stream(self):
        self.loading = True
        try:
            self.installs = getattr(self.client, self.detector).installs.to_dataframe()
            
            cb = self.get_callback(READERS[self.detector], MERGE_ON[self.detector], self.installs)
            self.stream =  PeriodicDataFrame(cb, interval=f"{self.interval}s")
            self.running_detector = self.detector
        finally:
            self.loading = False
        
    def update_plot(self):
        self.loading = True
        
        self.init_stream()
        
        if self.stream is None:
            return
        try:
            ngroups = len(self.installs[self.groupby].unique())
            self._plot = hvplot.plot(self.stream, kind="scatter", x=self.xaxis, y=self.yaxis, clabel="Rate [kb/s]",
                                 by=self.groupby, aspect=(2/ngroups+0.1), c="rate", s=200, alpha=0.8, responsive=True, 
                                 logz=True, cmap="coolwarm", subplots=True, backlog=BACKLOG[self.detector]).opts(
                            hv.opts.Scatter(colorbar_opts={"background_fill_color":"darkgrey"}) )
        finally:
            self.loading = False
        
    def start(self):
        self.init_stream()
        self.update_plot()
        
    @param.depends("_plot", "loading")
    def view(self):
        if self.loading:
            return CenterColumn(pn.indicators.LoadingSpinner(value=True))
        if self._plot is None:
            
            return pn.Column(self.param.start_button)
        else:
            return self._plot
        
    def settings(self):
        parameters = ["api_user", "api_key", "detector", "interval",
                      "xaxis", "yaxis", "groupby" ,"start_button", ]
        return pn.Param(self.param,
                         parameters=parameters,
                         width=250)
    @property
    def sections(self):
        return {
            "Live data rates": self.view,
        }

@login_required(pn.state)          
def view(db):
    # db = pn.state.as_cached(pn.state.curdoc.session_context.id, get_db)
    menu = session_menu(pn.state.curdoc.session_context.id)
    template = ListTemplate(
        title="Live data rates",
        sidebar_footer=menu,
    )
    pn.state.curdoc.theme = template.theme.bokeh_theme
    browser = RatesViewer(client=db)

    hv.renderer('bokeh').theme = template.theme.bokeh_theme
    template.main[:] = [CenterColumn("## "+k, v ,sizing_mode="stretch_both") for k,v in browser.sections.items()]
    template.sidebar[:] = [pn.panel(browser.settings)]
    return template


if __name__.startswith("bokeh"):
    view().servable()
