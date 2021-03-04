import param
import panel as pn
import holoviews as hv
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from xepmts.web_client.src.shared.templates import ListTemplate
from xepmts.web_client.src.shared import config, get_db
from xepmts.web_client.src.shared._menu import session_menu
from xepmts.web_client.src.shared._session import login_required
from xepmts.web_client.src.shared.models import BaseSection, DataLoader, CenterColumn


class HeatmapPlotter(BaseSection):
    xaxis = param.Selector(["date"], default="date")
    yaxis = param.Selector(["pmt_index"], default="pmt_index")
    color = param.Selector(["gain"], default="gain")
    extra_columns = param.List(["gain_err"])
    catagorical_axes = param.Boolean(default=True)
    groupby = param.Selector(["array"], default="array")
    aggregation = param.Selector(["mean", "median", "min", "max",])
    ncols = param.Integer(2)
    size = param.Integer(12)
    alpha = param.Number(0.9)
    colormap = param.Selector(hv.plotting.list_cmaps(), default="Plasma")
    
    selection = param.Parameter(precedence=-1)
    _plot = param.Parameter(precedence=-1)
    
    update_plot_action = param.Action(lambda self: self.update_plot(), label="Update Heatmap")

    def _init_view(self):
        self._view = pn.Column("Data not loaded yet.", sizing_mode="stretch_both")
        self._extra_columns = pn.widgets.MultiSelect(options=[], throttled=True)

    def _update_view(self, *events):
        if self.data is None:
            self.update_plot_action.disabled = True
        else:
            cols = list(self.data.columns)
            self.param.xaxis.objects = cols
            self.param.yaxis.objects = cols
            self.param.color.objects = [col for col in cols if is_numeric_dtype(self.data[col])]
            self._extra_columns.options = cols
            self.update_plot_action.disabled = False
            self.loading = True
            pn.state.add_periodic_callback(self.update_plot, count=1)
            
            
    @param.depends("loading", "_plot")
    def view(self):
        if self.loading:
            return CenterColumn(pn.indicators.LoadingSpinner(value=True),
                                sizing_mode="stretch_both")
            
        if self.data is None or not len(self.data):
            return pn.Column("# No data to show.")
        
        if self._plot is None:
            self.update_plot()

        return pn.Row(self._plot, self.selected_plot())

    def update_plot(self):
        self._plot = self.heatmap_plot()
        self.loading = False

    def heatmap_plot(self):
        if self.xaxis == self.yaxis:
            return pn.Column("X and Y axes are the same.")
        data = self.data.copy()
        if self.catagorical_axes:
            data.sort_values([self.xaxis, self.yaxis])
            for axis in [self.xaxis, self.yaxis]:
                if hasattr(data[axis], "dt"):
                    data[axis] = data[axis].dt.strftime('%Y-%m-%d')
                else:
                    data[axis] = data[axis].astype(str)
            
        aspect = len(self.data[self.xaxis].unique())/len(self.data[self.yaxis].unique())
        vdims = [self.color]+[col for col in self.extra_columns if col not in [self.xaxis, self.yaxis, self.color]]
        hm = hv.HeatMap(data, kdims=[self.xaxis, self.yaxis], vdims=vdims).aggregate(function=getattr(np, self.aggregation))
        hm = hm.opts(tools=["tap", "hover"], nonselection_alpha=0.4, aspect=aspect,
                     responsive=True, alpha=self.alpha, colorbar=True, colorbar_position='top', framewise=True,
                     xrotation=60, xaxis="top", cmap=self.colormap, min_width=600)
        self.selection = hv.streams.Tap(source=hm)
        
        return hm
    
    def selected_plot(self):
        if self.selection is None:
            return pn.Column()
        
        def tap_histogram(x, y):
#             hover = HoverTool(tooltips=[(dim, "@"+dim) for dim in ('cal_bins', "cal_counts")], mode="vline")
            key= (str(x), str(y).split(".")[0])
            # print(key, " Selected.")
            if x is None:
                c = hv.Curve(pd.DataFrame({'bin': [0,1,1,0], "counts": [0.4,0.4,0.5,0.5]}), 'bin', "counts")
                text = hv.Labels(pd.DataFrame({"x":[0.5], "y":[0.5], "text":["No calibration selected\n click on a calibration to view its data."]}), ['x', "y"], "text")
            else:
                counts = np.linspace(-100, 2500, 100)
                random_counts = 100*np.random.random(counts.shape) 
                random_counts += 1000*np.exp(-((counts-np.mean(counts))/2/1000)**2) 
                random_counts += 100*np.random.random(counts.shape) + 1500*np.exp(-(counts/2/50)**2)
                cal_data =  {"bin":counts,
                        "counts": random_counts
                                         }
                c = hv.Curve(pd.DataFrame(cal_data), 'bin', "counts")
                text = hv.Labels(pd.DataFrame({"x":[1000], "y":[1500], "text":["This is random data\n database is still empty"]}), ['x', "y"], "text")                         

            return c.opts(
                hv.opts.Curve(interpolation='steps-mid',framewise=True, height=400,tools=["hover"],
                            line_color='darkred',line_width=1, width=375, yaxis='right', logy=True),
                hv.opts.Labels(height=400, width=375)
                            )*text

        return pn.Column(hv.DynamicMap(tap_histogram, streams=[self.selection]),
                          hv.DynamicMap(tap_histogram, streams=[self.selection]))
    
    def settings(self):
        return pn.Column("### Heatmap options",
                        pn.Param(self.param, expand_button=False,  width=250, show_name=False,
                        parameters=["xaxis", "yaxis", "color", "alpha", "colormap", 
                                    "catagorical_axes", "extra_columns", "update_plot_action"],
                        widgets={"extra_columns": self._extra_columns}
                                 ), width=270, sizing_mode="fixed")
@login_required(pn.state)                    
def view(db):
    # db = pn.state.as_cached(pn.state.curdoc.session_context.id, get_db)
    menu = session_menu(pn.state.curdoc.session_context.id)
    template = ListTemplate(
        title="Heatmap viewer",
        sidebar_footer=menu,
    )
    pn.state.curdoc.theme = template.theme.bokeh_theme

    hm_plotter = HeatmapPlotter()
    loader = DataLoader(client=db, data_plotter=hm_plotter, _logged_in=db.logged_in)

    hv.renderer('bokeh').theme = template.theme.bokeh_theme
    template.main[:] = [pn.panel(c) for c in loader.cards()]
    template.sidebar[:] = [pn.panel(loader.settings)]

    return template


if __name__.startswith("bokeh"):
    view().servable()
