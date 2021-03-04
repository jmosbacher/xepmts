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



class TrendViewer(BaseSection):
    xaxis = param.Selector(["date"], default="date")
    yaxis = param.Selector(["gain"], default="gain")
    overlay = param.Selector(["pmt_index"], default="pmt_index")
    groupby = param.Selector(["sector"], default="sector")
    columns = param.Integer(1)
    alpha = param.Number(0.9)
    colormap = param.Selector(hv.plotting.list_cmaps(), default="Plasma")
    extra_columns = param.List(["gain_err"])
    loading = param.Boolean(False)
    
    _plots = param.Parameter()
    build_plots_button = param.Action(lambda self: self._update_view, label="Redraw plots")

    def _init_view(self):
        self._view = pn.Column(self.plots)

    def _update_view(self, *events):
        if self.data is None:
            return
        self.loading = True
        try:
            self._plots = self.make_plots()
        finally:
            self.loading = False

    @param.depends("_plots")
    def plots(self):
        if self._plots is None:
            button = pn.widgets.Button(name="Build plots",
                                       sizing_mode="stretch_width",
                                       height=150,
                                       button_type="primary")
            button.on_click(lambda event: self.make_plots())
            return pn.Column(button)
        return self._plots
    
    def make_holomap(self):
        curve_dict = {}
        for (overlay, groupby), pdf in self.data.groupby([self.overlay, self.groupby]):
            curve_dict[(overlay, groupby)] = hv.Curve(pdf.sort_values(self.xaxis), kdims=[self.xaxis], 
                                                      vdims=[self.yaxis], label=str(overlay), 
                                                      group=str(groupby)).opts(responsive=True,
                                                                               interpolation="steps-mid")
        holomap = hv.HoloMap(curve_dict, kdims=[self.overlay, self.groupby])
        return holomap
    
    def make_plots(self):
        holomap = self.make_holomap()
        overlay = holomap.overlay(self.overlay).opts(legend_position='top', legend_cols=True, legend_offset=(0, -10))
        plots = overlay.layout(self.groupby).cols(self.columns).opts(
            hv.opts.Curve(logy=False, height=300, show_title=False, interpolation="steps-mid",  ),    
        )
        return plots
 
    def settings(self):
        parameters = ["xaxis", "yaxis", "overlay", "groupby", "build_plots_button"]
        widgets = {}
        return pn.Param(self.param, 
                       parameters=parameters,
                       widgets=widgets
                       )


@login_required(pn.state)                    
def view(db):
    # db = pn.state.as_cached(pn.state.curdoc.session_context.id, get_db)
    menu = session_menu(pn.state.curdoc.session_context.id)
    template = ListTemplate(
        title="Heatmap viewer",
        sidebar_footer=menu,
    )
    pn.state.curdoc.theme = template.theme.bokeh_theme

    plotter = TrendViewer()
    loader = DataLoader(client=db, data_plotter=plotter, _logged_in=db.logged_in)

    hv.renderer('bokeh').theme = template.theme.bokeh_theme
    template.main[:] = [pn.panel(c) for c in loader.cards()]
    template.sidebar[:] = [pn.panel(loader.settings)]

    return template


if __name__.startswith("bokeh"):
    view().servable()
