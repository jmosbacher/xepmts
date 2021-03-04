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
from xepmts.web_client.src.shared.models import BaseSection, FilterTool, CenterColumn

DEFAULT_PLOT_NAMES = ["hist", "bar", "heatmap", "scatter", "bivariate",
 "hexbins", "step", "violin", "table", "line", "kde", "box"]
class ResourcePlots(param.Parameterized):
    
    filter_tool = param.ClassSelector(FilterTool)
    plot_name = param.Selector(DEFAULT_PLOT_NAMES)
    partition_size = param.Integer(5000)
    _plot = param.Parameter()
    overrides = param.Dict({})
    loading = param.Boolean(False)
    load_plot = param.Action(lambda self: self.update_plot())

    def _init_view(self):
        if self.filter_tool is None:
            return
        
    def __init__(self, **params):
        super().__init__(**params)
        if self.filter_tool is None:
            return
        def callback(event):
            self._update_plot_options()
        self.filter_tool.param.watch(callback, "resource",)    
        self._update_plot_options()

    @param.depends("loading")
    def view(self):
        if self.loading:
            return CenterColumn(pn.indicators.LoadingSpinner(value=self.loading),
                                sizing_mode="stretch_width")
        else:
            return pn.panel(self.plot_view)

    @param.depends("_plot")
    def plot_view(self, *events):
        if self._plot is None:
            return pn.Column("# Plot will load here.")
        else:
            return self._plot

    def update_plot(self):
        print(self.plot_name)
        if self.filter_tool is None:
            return
        if self.filter_tool.resource is None:
            return
        if not self.plot_name:
            return
        self.loading = True
        try:
            resource = self.filter_tool.get_filtered_resource()
            plotter = resource.paginate(self.partition_size).plot
            plot = getattr(plotter, self.plot_name)(**self.overrides)
            self._plot = pn.panel(plot, sizing_mode="stretch_both")
        finally:
            self.loading = False

    def _update_plot_options(self):
        if self.filter_tool.resource is None:
            return
        names = self.filter_tool.resource.plots + DEFAULT_PLOT_NAMES
        self.param.plot_name.names = {k:k for k in names}
        self.param.plot_name.objects = names
        if self.plot_name not in names and names:
            self.plot_name = names[0]

    def plot_selection_view(self):
        return pn.Column(
            self.param.plot_name,
            self.param.overrides,
            self.param.load_plot,
        )

    def settings(self):
        parameters = ["partition_size"]
        widgets = {"load_plot": pn.widgets.Button, "button_type": "primary"}
        plotting_settings = pn.Param(self.param,
                        parameters=parameters,
                        widgets=widgets,
                        show_name=False)
        return pn.Column(
                    "### Resource settings",
                    self.filter_tool.resource_settings,
                    plotting_settings,
                    pn.layout.Divider(margin=1),
                    "### PMT plot",
                    self.filter_tool.plot_settings,
                    width=270, sizing_mode="fixed")

    @property
    def sections(self):
        s = self.filter_tool.sections
        s["Plot selection"] = self.plot_selection_view
        s["Plot view"] = self.view
        return s

@login_required(pn.state)          
def view(db):
    # db = pn.state.as_cached(pn.state.curdoc.session_context.id, get_db)
    menu = session_menu(pn.state.curdoc.session_context.id)
    template = ListTemplate(
        title="Resource level plots",
        sidebar_footer=menu,
    )
    pn.state.curdoc.theme = template.theme.bokeh_theme

    browser = ResourcePlots(filter_tool=FilterTool(client=db))

    hv.renderer('bokeh').theme = template.theme.bokeh_theme
    template.main[:] = [pn.Card(v, header="## "+k ,sizing_mode="stretch_both") for k,v in browser.sections.items()]
    template.sidebar[:] = [pn.panel(browser.settings)]
    return template


if __name__.startswith("bokeh"):
    view().servable()
