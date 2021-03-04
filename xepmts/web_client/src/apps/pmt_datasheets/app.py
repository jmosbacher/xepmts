import param
import panel as pn
import holoviews as hv
import numpy as np
import base64
import pandas as pd
from pandas.api.types import is_numeric_dtype

from xepmts.web_client.src.shared.templates import ListTemplate
from xepmts.web_client.src.shared import config, get_db
from xepmts.web_client.src.shared._menu import session_menu
from xepmts.web_client.src.shared._session import login_required
from xepmts.web_client.src.shared.models import BaseSection, DataLoader, CenterColumn


def embed_pdf(pdf):
    if isinstance(pdf, bytes):
        pdf = base64.b64encode(pdf).decode()
    html = f"""
    <object width=100% height=100% data="data:application/pdf;base64,{pdf}" type="application/pdf">
    <p>Looks like your browser doesnt support embedding pdfs. Maybe time to upgrade?</p>
    </object>
    """
    return html

class DatasheetBrowser(param.Parameterized):
    client = param.Parameter()
    experiment = param.Selector()
    detector = param.Selector()
    data = param.DataFrame()
    _pmt_list = param.Parameter()
    _view = param.Parameter()
    _datasheet_view = param.Parameter()
    loading = param.Parameter()
    load_pmts_button = param.Action(lambda self: self.update_pmt_list(), label="Show PMTs")
    show_datasheet_button = param.Action(lambda self: self.show_datasheet(), label="Show datasheet")
    
    def __init__(self, **params):
        super().__init__(**params)
        self.update_menu()
    
    @param.depends("client", watch=True)
    def _update_experiment_options(self):
        if self.client is None:
            return
        experiments = {"xenonnt": self.client,
                    "xenon1t": self.client.xenon1t}
        self.param.experiment.names = experiments
        self.param.experiment.objects = [self.client, self.client.xenon1t]
        if self.experiment not in experiments.values():
            self.experiment = self.client
        
    @param.depends("experiment", watch=True)
    def _update_detector_options(self):
        if self.experiment is None:
            return
        detectors = {k:v for k,v in self.experiment.sub_resources.items() 
                     if k not in self.param.experiment.names}
        self.param.detector.objects = list(detectors.values())
        self.param.detector.names = detectors
        if self.detector not in detectors.values():
            self.detector = detectors.get("tpc", list(detectors.values())[0])
    
    def update_menu(self):
        with param.discard_events(self):
            self._update_experiment_options()
            self._update_detector_options()
            
    def update_pmt_list(self):
        if self.detector is None:
            return
        self.loading = True
        try:
            pmts = self.detector.pmts.project(datasheet=0).to_dataframe()
            installs = self.detector.installs.df
            self.data = pmts.merge(installs)
            self._pmt_list = pn.widgets.DataFrame(self.data, sizing_mode="stretch_width", height=250)
        finally:
            self.loading = False
            
    def download_selected(self):
        if self._pmt_list is None or not self._pmt_list.selection:
            return b""
        data = self.data.reset_index()
        sn = data["serial_number"].iloc[self._pmt_list.selection[0]]
        query = {"serial_number": sn}
        return self.detector.pmts.find_one_item(query=query).datasheet
    
    def show_datasheet(self):
        self.loading = True
        try:
            pdf = self.download_selected()
            if pdf:
                self._datasheet_view = pn.pane.HTML(embed_pdf(pdf),
                                                    sizing_mode="stretch_both")
        finally:
            self.loading = False
    
    @param.depends("_pmt_list", "loading")
    def pmt_list(self):
        if self.loading:
            return CenterColumn(pn.indicators.LoadingSpinner(value=True),
                             sizing_mode="stretch_both" )
        if self._pmt_list is None:
            button = pn.widgets.Button(name="Load PMT list", button_type="primary",
                                 sizing_mode="stretch_width", height=200)
            button.on_click(lambda event: self.update_pmt_list())
            return pn.Column(button, sizing_mode="stretch_width")
        else:
            load_button = pn.widgets.Button(name="Load Selected Datasheet", button_type="primary",
                                 sizing_mode="stretch_width", height=50)
            load_button.on_click(lambda event: self.show_datasheet())
            return pn.Column(self._pmt_list,
                             load_button,
                             sizing_mode="stretch_both")
        
    @param.depends("_datasheet_view",)
    def datasheet_view(self):
        if self._datasheet_view is None:
            return CenterColumn(pn.panel("# No datasheet loaded yet.", sizing_mode="stretch_both"), sizing_mode="stretch_both")
        return pn.Column(self._datasheet_view,
                        sizing_mode="stretch_width",
                        height=900)
    
    @param.depends("data",)
    def view(self):
        return pn.Column(self.pmt_list,
                        self.datasheet_view,
                        sizing_mode="stretch_both")
    @property
    def sections(self):
        return {
            "Datasheet List": self.pmt_list,
            "Datasheet viewer": self.datasheet_view,
        }
    
    def settings(self):
        
        return pn.Param(self.param,
                       parameters=["experiment", "detector", "load_pmts_button"],
                       
                       expand_button=False)

@login_required(pn.state)                    
def view(db):
    # db = pn.state.as_cached(pn.state.curdoc.session_context.id, get_db)
    menu = session_menu(pn.state.curdoc.session_context.id)
    template = ListTemplate(
        title="PMT Datasheets",
        sidebar_footer=menu,
    )
    pn.state.curdoc.theme = template.theme.bokeh_theme

    browser = DatasheetBrowser(client=db)

    hv.renderer('bokeh').theme = template.theme.bokeh_theme
    template.main[:] = [pn.Card(v, header="## "+k, sizing_mode="stretch_both") for k,v in browser.sections.items()]
    template.sidebar[:] = [pn.panel(browser.settings)]
    return template


if __name__.startswith("bokeh"):
    view().servable()
