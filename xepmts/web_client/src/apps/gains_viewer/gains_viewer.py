import xepmts
import holoviews as hv
import param
import panel as pn
import pandas as pd
import numpy as np
import httpx
import asyncio
import time
import eve_panel
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from functools import cache
from panel.io.server import unlocked
from tornado.ioloop import IOLoop

pn.config.sizing_mode = "stretch_width"
executor = ThreadPoolExecutor(max_workers=4)


def get_field_limit(resource, field="timestamp", sort=""):
    sort = sort + field
    r = resource.find(projection={field: 1}, sort=sort, max_results=1)
    return pd.to_datetime(r[0][field])

def get_date_range(resource, field="timestamp"):
    return get_field_limit(resource, field=field), get_field_limit(resource, field=field, sort="-")

def CenterColumn(*objs, **kwargs):
    for obj in objs:
        obj.align = "center"
#     kwargs["margin"] = kwargs.get("margin", 1)
    return pn.Column(pn.layout.VSpacer(), *objs, pn.layout.VSpacer(), **kwargs)

def CenterRow(*objs, **kwargs):
    for obj in objs:
        obj.align = "center"
    kwargs["margin"] = kwargs.get("margin", 5)
    return pn.Column(pn.layout.HSpacer(), *objs, pn.layout.HSpacer(), **kwargs)


class GainsViewer(param.Parameterized):
    PMT_PLOT_SETTINGS = ["experiment", "detector",
                         "color_column", "alpha", "ncols", "colormap"]
    client = param.Parameter(default=None)
    experiment = param.Selector()
    detector = param.Selector()
    date_range = param.DateRange()
    
    _pmt_selection_plot = param.Parameter(precedence=-1)
    _selected_pmts_table = param.Parameter(precedence=-1)
    _gains_plot = param.Parameter(precedence=-1)
    
    selected = param.DataFrame(precedence=-1)
    
    ncols = param.Integer(2)
    color_column = param.Selector()
    alpha = param.Number(0.5)
    colormap = param.Selector(hv.plotting.list_cmaps(), default="Set1")
    
    load_pmt_selection = param.Action(lambda self: self._load_pmt_selection_pressed(), label="Select pmts")
    load_gains_map = param.Action(lambda self: self._load_gains_pressed(), label="Load data")
    
    gains = param.DataFrame(precedence=-1)
    
    _loading = param.Boolean(False)
    _npages = param.Integer(100)
    _loaded = param.Integer(0)

    _main = param.Parameter(precedence=-1)
    _selections = param.Parameter(precedence=-1)
    _installs = param.Parameter(precedence=-1)
    _installs_cache = param.Dict({})
    _pages = param.List([])
    _cb = param.Parameter(precedence=-1)
    _done_loading = param.Boolean(False)
    _logged_in = param.Boolean(False)
    
    def main_view(self):
        if self._main is None:
            self._main = pn.Column(
                *self.panels(),
                sizing_mode="stretch_both"
                              )
        self._update_menu()
        return self._main
    
    def panels(self):
        return [
            pn.panel(self.pmt_selection_plot),
            pn.panel(self.selected_pmts_table),
            pn.panel(self.gains_plot),
        ]
    
    def __init__(self, **params):
        super().__init__(**params)
        self._update_menu()

    def _update_login_status(self):
        self._logged_in = self.client.logged_in

    @param.depends("_pmt_selection_plot", "_logged_in")
    def pmt_selection_plot(self):
        if self._pmt_selection_plot:
            content = self._pmt_selection_plot
        elif self.client.logged_in:
        
            button = pn.widgets.Button(name="Load PMT maps",
                                       width=400, height=200, 
                                       max_height=200, sizing_mode="stretch_width")
            def cb(event):
                self._load_pmt_selection_pressed()

            button.on_click(cb)
            content = CenterColumn(button, sizing_mode="stretch_both", )
        else:
            
            content = pn.panel("### Database access needed. \nYou must login before using this page.")
        view = pn.Card(content, header="## PMT Selection", sizing_mode="stretch_both",)
        def collapse_view(event):
            if event.old==False and event.new==True:
                view.collapsed = True
        self.param.watch(collapse_view, ["_loading"])

        def reset_view(*events):
            self._pmt_selection_plot = None
            self.gains = None
        self.param.watch(reset_view, ["experiment", "detector"])

        return view

    @param.depends("_selected_pmts_table")
    def selected_pmts_table(self):
        if self._selected_pmts_table is None:
            content = CenterColumn(sizing_mode="stretch_width")
        else:
            content = self._selected_pmts_table
        view = pn.Card(content, header="## Selected PMT details",
                       collapsed=False, sizing_mode="stretch_both")
        def collapse_view(event):
            if event.old==False and event.new==True:
                view.collapsed = True
        self.param.watch(collapse_view, ["_loading"])
        return view
        
    @param.depends("client")
    def _update_experiment_options(self):
        if self.client is None:
            return
        self.param.experiment.names = {"xenonnt": self.client, "xenon1t": self.client.xenon1t}
        self.param.experiment.objects = [self.client, self.client.xenon1t]
        self.experiment = self.client
        
    @param.depends("experiment", watch=True)
    def _update_detector_options(self):
        if self.experiment is None:
            return
        detectors = {k:v for k,v in self.experiment.sub_resources.items() 
                     if k not in self.param.experiment.names}
        self.param.detector.objects = list(detectors.values())
        self.param.detector.names = detectors
        self.detector = detectors.get("tpc",list(detectors.values())[0])
    
    @param.depends("detector","_logged_in", watch=True)
    def _update_plotting_options(self):
        if self.detector is None:
            return
        try:    
            self.param.color_column.objects = list(
                self.detector.installs.find_df(max_results=1).dropna(axis=1, how="all").columns)
        except:
            pass
        self.color_column = "sector"
        try:
            drange = get_date_range(self.detector.gains)
        except:
            drange = pd.to_datetime("21/3/2019"), pd.to_datetime(time.time()*1e9)
        self.param.date_range.softbounds = drange
        self.date_range = drange
        

    @param.depends("_logged_in", watch=True)
    def _update_menu(self):
        if self.experiment is None:
            self._update_experiment_options()
        if self.detector is None:
            self._update_detector_options()
        if self.color_column is None or self.date_range is None:
            self._update_plotting_options()
    
    @property
    def installs(self):
        if self.detector is None:
            return hv.Table(pd.DataFrame({
                "pmt_index": [], "array":[], "position_x": [], "position_y": []}))

        key = self.experiment.name + self.detector.name
        if key not in self._installs_cache:
            installs = self.detector.installs.paginate(300).df.dropna(axis=1, how="all")
            self._installs_cache[key] = hv.Table(installs)
        return self._installs_cache[key]
    
    def _load_gains_pressed(self):
        if self._loading:
            return "Already loading"
        if self._cb is not None and self._cb.running:
            self._cb.stop()
            
        self._loading = True
        self.gains = None
        self._pages = []
        try:
            indices = self.selected_pmts()
            gains = self.detector.gains
            date_min, date_max = self.date_range
            if len(indices):
                gains = gains.paginate(500).filter(
                    pmt_index={"$in": indices},
                    timestamp={"$gt": date_min.timestamp()*1e9, "$lt": date_max.timestamp()*1e9},)
            self._npages = len(gains.page_numbers)
            def cb(idx):
                self._loaded += 1
        except Exception as e:
            self._loading = False
            return e
        loop = IOLoop.current()
        for idx in gains.page_numbers:
            future = executor.submit(gains.get_page, idx)
            loop.add_future(future, self._update_gains)
        self._cb = pn.state.add_periodic_callback(self._check_gains_loaded)

   
    def _update_gains(self, future):
        page = None
        try:
            page = future.result()
            if not self._loading:
                return
        except:
            pass
        finally:
            with unlocked():
                if page:
                    self._pages.append(page)
                self._loaded += 1
            

    def _check_gains_loaded(self):
        if not self._loading:
            self._pages = []
            if self._cb is not None and self._cb.running:
                self._cb.stop()
                return

        if len(self._pages)<self._npages:
            return

        with unlocked():
            try:
                df = pd.concat([page.to_dataframe() for page in self._pages])
                df["pmt_index"] = df["pmt_index"].astype(str)
                df = df.sort_values(["pmt_index", "timestamp"])
                df["date"] = pd.to_datetime(df["timestamp"]).dt.strftime('%Y-%m-%d')
                df = df.replace(-np.inf, np.nan)
                df = df.replace(np.inf, np.nan)
                self.gains = df
            except:
                pass
            finally:
                self._loading = False
            
    def _load_pmt_selection_pressed(self):
        spinner = pn.indicators.LoadingSpinner(value=True, width=150, height=150, align='center')
        self._pmt_selection_plot = CenterColumn(spinner, sizing_mode="stretch_width", )
        pn.state.add_periodic_callback(self.load_pmt_arrays, count=1)
        
    @param.depends("ncols", "color_column", "alpha", "colormap",)
    def pmt_arrays(self):
        installs = self.installs
        cols = [dim.name for dim in installs.dimensions()]
   
        arrays = np.unique(installs["array"])
        extra_cols = [col for col in cols if col not in ["position_x", "position_y"]]
        pmt_plot = hv.Points(installs, kdims=["position_x", "position_y"], vdims=extra_cols).opts(
                    alpha=self.alpha, color=self.color_column, size=15, 
                    nonselection_alpha=0.1, cmap=self.colormap, colorbar=True,
        )
        array_plots = {array: pmt_plot.select(array=array).opts(default_tools=["tap", "hover", "lasso_select"], 
                                                                aspect=1.1, height=300, responsive=True) for array in arrays}
        self._selections = [hv.streams.Selection1D(source=array_plots[array], throttle_timeout=1000, throttle_scheme="throttle").rename(index=f"{array}") for array in arrays ]
        
        def make_table(**kwargs):
            dfs = []
            for array, idx in kwargs.items():
                if idx:
                    dfs.append(self.installs.select(array=array).iloc[idx].dframe())
                else:
                    dfs.append(self.installs.select(array=array).dframe())
            if not len(dfs):
                return self.installs
            df = pd.concat(dfs).reset_index()
            table = hv.Table(df).opts(
                hv.opts.Table(width=900, fit_columns=True)
            )
            return table

        self._selected_pmts_table = CenterColumn(hv.DynamicMap(make_table, streams=self._selections),
                                                    sizing_mode="stretch_width") 
        
        
        return hv.NdLayout(array_plots, kdims="array").cols(self.ncols)
   
    def load_pmt_arrays(self):
        button = pn.widgets.Button(name="Click to load gains for selection",
                                       width=400, height=70,
                                       max_height=100, sizing_mode="stretch_width")
        def load_gains(event):
            self._load_gains_pressed()

        button.on_click(load_gains)
        plot_wrapper = pn.Column(self.pmt_arrays,
                                 sizing_mode="stretch_both", height=370, margin=10)
        self._pmt_selection_plot = pn.Column(plot_wrapper, 
                                            pn.Param(self.param.date_range),
                                            button,
                                            height=500,
#                                                 max_height=500,
                                            sizing_mode="stretch_both")
    
    def selected_pmts(self):
        if not self._selections:
            return []
        installs = self.installs
        pmt_indices = []
        for s in self._selections:
            array = s._rename["index"]
            if s.index:
                table = installs.select(array=array).iloc[s.index]
            else:
                table = installs.select(array=array)
            pmt_indices.extend([int(x) for x in table.dimension_values("pmt_index")])
        return pmt_indices
    

    @param.depends("_loaded", "_loading")
    def progress(self):
        bar = pn.indicators.Progress(value=self._loaded, active=self._loading, max=self._npages,
                                    sizing_mode="stretch_width", margin=10, min_width=300)
        perc = int(100*self._loaded/self._npages)
        text = pn.widgets.StaticText(value=f"Loading requested data. {perc}% [{self._loaded}/{self._npages} pages] done.", 
                                    align="center")
        return CenterColumn(text, bar, sizing_mode="stretch_width",)

    @param.depends("gains", "_loading")
    def gains_plot(self):
        if self._loading:
            cancel = pn.widgets.Button(name="Cancel", sizing_mode="stretch_width")
            def cancel_pressed(event):
                self._loading = False
            cancel.on_click(cancel_pressed)
            
            progress = pn.panel(self.progress)
            content = pn.Column(
                                progress,
                                cancel,
                                sizing_mode="stretch_width")

        elif self.gains is None or not len(self.gains):
            content = CenterColumn(pn.panel("Gains visualizations will be shown here after being loaded."),
                                   sizing_mode="stretch_both")
        else:
            aspect = len(self.gains["date"].unique())/len(self.gains["pmt_index"].unique())
            hm = hv.HeatMap(self.gains, kdims=["date", "pmt_index"], vdims=["gain", "gain_err"]).aggregate(function=np.mean)
            hm = hm.opts(tools=["tap", "hover"], nonselection_alpha=0.1, aspect=aspect, responsive=True
                          ,xrotation=60, xaxis="top")
            content = pn.Column(hm, sizing_mode="stretch_both", height=600, width=700)
        return pn.Card(content, header="## Gains plot", sizing_mode="stretch_both")


    def settings_view(self):
        return pn.Column(pn.Param(self.param, expand_button=False,  width=250,
                        parameters=self.PMT_PLOT_SETTINGS), width=270, sizing_mode="fixed")
    