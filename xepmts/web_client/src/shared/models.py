"""Provides the following models used to create the site

- Application
- Person
- Resource
- SiteConfig

"""

from copy import deepcopy

import param
import panel as pn
import holoviews as hv
import pandas as pd
import numpy as np
import logging
import time

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from panel.io.server import unlocked
from tornado.ioloop import IOLoop

from awesome_panel_extensions.site.application import Application
from awesome_panel_extensions.site.author import Author as Person
from awesome_panel_extensions.site.resource import Resource
from awesome_panel_extensions.site.site_config import SiteConfig as _ApSiteConfig
from awesome_panel_extensions.io.loading import start_loading_spinner, stop_loading_spinner

from eve_panel.utils import to_json_compliant

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=8)

class SiteConfig(_ApSiteConfig):
    pass
    
def CenterColumn(*objs, **kwargs):
    for obj in objs:
        if hasattr(obj, "align"):
            obj.align = "center"
    kwargs["margin"] = kwargs.get("margin", 5)
    return pn.Column(pn.layout.VSpacer(), *objs, pn.layout.VSpacer(), **kwargs)

def CenterRow(*objs, **kwargs):
    for obj in objs:
        if hasattr(obj, "align"):
            obj.align = "center"
    kwargs["margin"] = kwargs.get("margin", 5)
    return pn.Column(pn.layout.HSpacer(), *objs, pn.layout.HSpacer(), **kwargs)

def get_field_limit(resource, field="timestamp", sort=""):
    sort = sort + field
    r = resource.find(projection={field: 1}, sort=sort, max_results=1)
    return pd.to_datetime(r[0][field])

def get_date_range(resource, field="timestamp"):
    return get_field_limit(resource, field=field), get_field_limit(resource, field=field, sort="-")

class BaseSection(param.Parameterized):
    """Abstract Class for Section of App"""

    data = param.DataFrame(allow_None=True)
    loading = param.Boolean(default=False)
    _view = param.ClassSelector(class_=pn.Column)
    
    @param.depends("loading", "_view")
    def view(self):
        if self.loading or self._view is None:
            return CenterColumn(pn.indicators.LoadingSpinner(value=self.loading),
                                sizing_mode="stretch_both")
        else:
            return self._view

    @property
    def sections(self):
        return {"View": self.view}

    def cards(self):
        cards = [pn.Card(section, header="### "+name, sizing_mode="stretch_both")
                 for name,section in self.sections.items()]
        return cards

    def __init__(self, **params):
        super().__init__(**params)
        self._init_view()
        self._update_view()
        self.param.watch(self._update_view, "data")

    def _init_view(self):
        raise NotImplementedError()

    def _update_view(self, *events):
        raise NotImplementedError()

        
DEFAULT_DRANGE = pd.to_datetime("21/3/2019"), pd.to_datetime(time.time()*1e9)

class FilterTool(BaseSection):
    client = param.Parameter(precedence=-1)
    experiment = param.Selector(precedence=0)
    detector = param.Selector(precedence=1)
    reload_info_action = param.Action(lambda self: self.load_pmt_data(), label="Reload PMT info", precedence=2)
    resource = param.Selector(precedence=3)

    date_range = param.DateRange(default=DEFAULT_DRANGE, softbounds=DEFAULT_DRANGE, precedence=1)
    filters = param.Dict(default={}, precedence=2)
    projection = param.List([], precedence=3)
    color_selection = param.List([], precedence=4)

    xaxis = param.Selector(["position_x"], default="position_x", precedence=4)
    yaxis = param.Selector(["position_y"], default="position_y", precedence=5)
    time_field = param.Selector(["timestamp", "date", "datetime"], default="timestamp", precedence=6)
    color = param.Selector(["sector"], default="sector", precedence=7)
    groupby = param.Selector(["array"], default="array", precedence=6)
    ncols = param.Integer(2, precedence=8)
    size = param.Integer(12, precedence=8)
    alpha = param.Number(0.5, precedence=8)
    colormap = param.Selector(hv.plotting.list_cmaps(), default="Set1", precedence=7)
    
    _selections = param.Parameter(precedence=-1)

    _group_plots = param.Parameter(precedence=-1)
    _details_table = param.Parameter(precedence=-1)

    _installs_cache = param.Dict({}, precedence=-1)

    update_plot_action = param.Action(lambda self: self.update_plot(), label="Update PMT Plot", precedence=9)
    
    
    
    def _init_view(self):
        self._view = pn.Column("PMT data not loaded yet.", sizing_mode="stretch_both")
        self._update_menu()
        
    def _update_view(self, *events):
        if self.data is None:
            pass
        else:
            cols = list(self.data.columns)
            self.param.xaxis.objects = cols
            self.param.yaxis.objects = cols
            self.param.color.objects = cols
            self.param.groupby.objects = cols
            self.update_plot()
            
    @param.depends("loading")
    def view(self):
        if self.loading:
            return CenterColumn(pn.indicators.LoadingSpinner(value=self.loading),
                                sizing_mode="stretch_width")
        if self.data is None:
            button = pn.widgets.Button(name="Select PMTs", button_type="primary",
                                    sizing_mode="stretch_width", height=150)
            def cb(event):
                self.load_pmt_data()
            button.on_click(cb)
            return CenterColumn(button, sizing_mode="stretch_width")
        else:
            return pn.panel(self._group_plots)

    def _update_experiment_options(self):
        if self.client is None:
            return
        
        experiments = {"xenonnt": self.client, "xenon1t": self.client.xenon1t}
        self.param.experiment.names = experiments
        self.param.experiment.objects = [self.client, self.client.xenon1t]
        if self.experiment not in experiments.values():
            self.experiment = experiments.get("xenonnt", list(experiments.values())[0])
        
    @param.depends("experiment", watch=True)
    def _update_detector_options(self):
        if self.experiment is None:
            return
        
        detectors = {k:v for k,v in self.experiment.sub_resources.items() 
                     if k not in self.param.experiment.names}
        self.param.detector.names = detectors
        self.param.detector.objects = list(detectors.values())
        if self.detector not in detectors.values():
            self.detector = detectors.get("tpc", list(detectors.values())[0])
        
    @param.depends("detector", watch=True)
    def _update_resource_options(self):
        if self.detector is None:
            return
        
        resources = self.detector.resources
        self.param.resource.names = resources
        self.param.resource.objects = list(resources.values())
        if self.resource not in resources.values():
            self.resource = resources.get("gains",list(resources.values())[0])
    
    @param.depends("resource", watch=True)
    def _update_date_range_options(self):
        try:
            drange = get_date_range(self.resource, field=self.time_field)
        except:
            drange = pd.to_datetime("21/3/2019"), pd.to_datetime(time.time()*1e9)
        self.param.date_range.softbounds = drange
        self.date_range = drange
       
    def _update_plotting_options(self):
        if self.detector is None:
            return
        cols = list(self.detector.installs.schema)
        self.param.xaxis.objects = cols
        self.param.yaxis.objects = cols
        self.param.color.objects = cols
        self.param.groupby.objects = cols
        
    def _update_menu(self):
        with param.batch_watch(self):
            self._update_experiment_options()
            self._update_detector_options()
            self._update_resource_options()
#             self._update_date_range_options()
            self._update_plotting_options()
        
    def update_plot(self):
        self.loading = True
        try:
            self._group_plots = self.make_group_plots()
            self._details_table = self.make_details_table()
        finally:
            self.loading = False

    def make_group_plots(self):
        installs = hv.Table(self.data)
        cols = list(self.data.columns)
        groups = list(sorted(self.data[self.groupby].unique(), reverse=True))
        extra_cols = [col for col in cols if col not in [self.xaxis, self.yaxis]]
        
        pmt_plot = hv.Points(installs, kdims=[self.xaxis,self.yaxis], vdims=extra_cols).opts(
                    alpha=self.alpha, color=self.color, size=self.size, responsive=True,
                    nonselection_alpha=0.1, cmap=self.colormap, colorbar=True, default_tools=["tap", "hover", "lasso_select"],
        )
        labels = hv.Labels(installs, kdims=[self.xaxis,self.yaxis], vdims=["pmt_index", self.groupby])

        plots = {group: pmt_plot.select(**{self.groupby: group}) for group in groups}
        self._selections = [hv.streams.Selection1D(source=plots[group],).rename(index=f"{group}")
                            for group in groups ]                        
        for k,v in plots.items():
            plots[k] = v*labels.select(**{self.groupby:k})
        if self.xaxis == "position_x" and self.yaxis=="position_y":
            tpc_wall = hv.Ellipse(0,0, 134, kdims=["position_x", "position_y"]).opts(color="white")
            for k,v in plots.items():
                plots[k] = tpc_wall*v

        layout =  hv.NdLayout(plots, kdims=self.groupby).cols(self.ncols).opts(
            hv.opts.Points(framewise=True, aspect=1.1, min_width=350, responsive=True,
                            default_tools=["tap", "hover", "lasso_select"]),
            hv.opts.Ellipse(default_tools=[]),
            hv.opts.Labels(text_font_size="6px", default_tools=[]),
            )
        
        return layout

    def make_details_table(self):
        installs = hv.Table(self.data)
        def make_table(**kwargs):
            dfs = []
            for group, idx in kwargs.items():
                if idx:
                    dfs.append(installs.select(**{self.groupby: group}).iloc[idx].dframe())
                else:
                    dfs.append(installs.select(**{self.groupby: group}).dframe())
            if not len(dfs):
                return installs
            df = pd.concat(dfs).reset_index()
            table = hv.Table(df).opts(
                hv.opts.Table(width=900, fit_columns=True)
            )
            return table

        return hv.DynamicMap(make_table, streams=self._selections)

    def details_table(self):
        if self._details_table is None:
            return pn.Column()
        else:
            return self._details_table

    def selected_pmts(self):
        if self._selections is None:
            return []
        installs = hv.Table(self.data)
        pmt_indices = []

        for s in self._selections:
            group = s._rename["index"]
            filters = {self.groupby: group}
            if s.index:
                table = installs.select(**filters).iloc[s.index]
            else:
                table = installs.select(**filters)
            if len(self.color_selection):
                table = table.select(**{self.color: self.color_selection})
            pmt_indices.extend([int(x) for x in table.dimension_values("pmt_index")])
        return pmt_indices

    @param.depends("color", "data")
    def extra_filters_section(self):
        if self.data is None:
            options = []
        else:
            options = [to_json_compliant(x) for x in self.data[self.color].unique()][:50]
        name = self.color
        if not name.endswith("s"):
            name += "s"
        multi_select = pn.widgets.MultiChoice(name=name, value=options,
                                            options=options, height=200)

        widgets = {
            "date_range": {"type": pn.widgets.DateRangeSlider,
                           "sizing_mode": "stretch_width",
                           },
            "color_selection": multi_select

        }
        parameters = ["date_range", "color_selection" ,"filters"]
        return pn.Param(self.param,
                        parameters=parameters,
                        widgets=widgets,
                        expand_button=False,
                        show_name=False,
                        sizing_mode="stretch_width")

    
    def settings(self):
        return pn.Column(
                    "### Resource settings",
                    self.resource_settings,
                    pn.layout.Divider(margin=1),
                    "### PMT plot",
                    self.plot_settings,
                    width=270, sizing_mode="fixed")
        
    
    def resource_settings(self):
        parameters = ["experiment", "detector", "resource", "reload_info_action",]
        widgets = {}
        return pn.Param(self.param, 
                        parameters=parameters,
                        widgets=widgets,
                        expand_button=False,
                        width=250, show_name=False,)
        
        
    def plot_settings(self):
        parameters = ["groupby","xaxis","yaxis","ncols","color","alpha",
                        "colormap","size", "update_plot_action"]
        widgets = {}
        return pn.Param(self.param, 
                        parameters=parameters,
                        widgets=widgets,
                        expand_button=False,
                        width=250, show_name=False,)

    def pre_pmt_load(self):
        self.loading = True
       
    def on_pmt_load_success(self):
        self.pmt_data_loaded = True
        
    def post_pmt_load(self):
        self.loading = False
        
    def load_pmt_data(self):
        if self.client is None or not self.client.logged_in:
            return
        if self.detector is None:
            return
        self.pre_pmt_load()
     
        key = self.experiment.name + self.detector.name
        if key in self._installs_cache:
            self.data = self._installs_cache[key]
            self.post_pmt_load()
        else:
            resource = self.detector.installs
            future = executor.submit(resource.to_dataframe)
            def cb(future):
                try:
                    data = future.result()
                    self.data = data
                    self._installs_cache[key] = data
                    self.on_pmt_load_success()
                finally:
                    self.post_pmt_load()
            IOLoop.current().add_future(future, cb)

    def get_filtered_resource(self):
        resource = self.resource
        date_min, date_max = self.date_range
        filters = dict(self.filters)
        if self.time_field in resource.schema:
            filters[self.time_field] = {"$gt": date_min.timestamp()*1e9, "$lt": date_max.timestamp()*1e9}
        indices = self.selected_pmts()
        if len(indices):
            filters["pmt_index"] = {"$in": indices}
        resource = resource.filter(**filters)
        return resource

    @property
    def sections(self):
        self._update_menu()
        return {
            "PMT Selection": self.view,
            "Selection details": self.details_table,
            "Additional filters": self.extra_filters_section,
        }
      
    def panels(self):
        return [pn.panel(s) for s in self.sections.values()]
    
    def cards(self):
        cards = [pn.Card(section, header="### "+name, sizing_mode="stretch_both") for name,section in self.sections.items()]
        cards[1].collapsed = True
        return cards


class DataLoader(param.Parameterized):
    filter_tool = param.ClassSelector(FilterTool)
    data_plotter = param.ClassSelector(BaseSection)
    client = param.Parameter(default=None)
    
    merge_pmt_info = param.Boolean(True)
    _data_plot = param.Parameter(precedence=-1)
    data = param.DataFrame()
    resource_name = param.String()
    partition_size = param.Integer(500)
    
    loading = param.Boolean(False)
    _npages = param.Integer(100)
    _ndocs = param.Integer(100)
    _loaded = param.Integer(0)
    
    _view = param.ClassSelector(pn.Column, precedence=-1)
    _selections = param.Parameter(precedence=-1)
    
    _loaded_data_cache = param.List([], precedence=-1)
    _cb = param.Parameter(precedence=-1)
    _logged_in = param.Boolean(False)

    def __init__(self, **params):
        params["filter_tool"] = params.pop("filter_tool", FilterTool(client=params["client"]))
        super().__init__(**params)

    def view(self):
        if self._view is None:
            self._view = pn.Column(
                *self.cards(),
                sizing_mode="stretch_both"
                              )
        return self._view
    
    @property
    def sections(self):
        sections = {}
        sections.update(self.filter_tool.sections)
        sections["Data loading"] = self.loader_section
        sections.update(self.data_plotter.sections)
        return sections

    @param.depends("loading")
    def loader_section(self):
        if self.loading:
            return self.progress
        else:
            load_data = pn.widgets.Button(name="Load data", 
            height=50, button_type="primary")
            load_data.on_click(lambda event: self.load_data())
            return CenterColumn(load_data,
                                sizing_mode="stretch_both")

    def panels(self):
        return [pn.panel(s) for s in self.sections.values()]
    
    def cards(self):
        cards = [pn.Card(section, header="### "+name, sizing_mode="stretch_both") for name,section in self.sections.items()]
        cards[1].collapsed = True
        return cards

    def _update_login_status(self):
        self._logged_in = self.client.logged_in

    def pre_data_load(self):
        self.loading = True
        if self._cb is not None and self._cb.running:
            self._cb.stop()
        self._loaded = 0
        self._loaded_data_cache = []
        self.data_plotter.loading = True
        self.data_plotter.data = None

    def on_data_load_task_complete(self):
        self._loaded += 1
        logger.info(f"Data loading task {self._loaded} completed.")

    def on_data_load_task_success(self):
        logger.info("Data loading task completed successfully.")

    def on_data_load_success(self):
        self.data_loaded = True
        logger.info("Data loaded successfully.")
        
    def post_data_load(self):
        self.data_plotter.loading = False
        self._loaded_data_cache = []
        if self._cb is not None and self._cb.running:
            self._cb.stop()
        self.loading = False
        logger.info("Data loading completed.")

    def load_data(self):
        if self.loading:
            return "Busy"
        self.pre_data_load()
        try:
            resource = self.filter_tool.get_filtered_resource().paginate(self.partition_size)
            page_numbers = resource.page_numbers
            if not page_numbers:
                self.post_data_load()
                return
            self._npages = len(page_numbers)
            self._ndocs = resource.nitems
            loop = IOLoop.current()
            for idx in page_numbers:
                future = executor.submit(resource.get_page_raw, idx)
                loop.add_future(future, self._data_ready_cb)
            self._cb = pn.state.add_periodic_callback(self._check_data_loading_done, period=1000)
        except Exception as e:
            logger.error("Exception raised while starting data loading jobs: "+str(e))
        
    def _data_ready_cb(self, future):
        try:
            page = future.result()
            if not self.loading:
                return
            with unlocked():
                self._loaded_data_cache.extend(page)
                self.on_data_load_task_success()
        except Exception as e:
                logger.error(str(e))
        finally:
            self.on_data_load_task_complete()
            
    def _check_data_loading_done(self):
        if not self.loading:
            self.post_data_load()
            return

        if self._loaded<self._npages:
            return

        with unlocked():
            try:
                self.process_loaded_data()
                self.on_data_load_success()
            except Exception as e:
                logger.error(str(e))
            finally:
                self.post_data_load()
                
    def process_loaded_data(self):
        df = pd.DataFrame(self._loaded_data_cache)
        df = df[[col for col in df.columns if not col.startswith("_")]]
        if "timestamp" in df.columns and "date" not in df.columns:
            df["date"] = pd.to_datetime(df["timestamp"])
            # .dt.strftime('%Y-%m-%d')
        df = df.replace(-np.inf, np.nan)
        df = df.replace(np.inf, np.nan)
        if self.merge_pmt_info:
            df = pd.merge(df, self.filter_tool.data).dropna(axis=1, how="all").reset_index(drop=True)
        self.data_plotter.data = df
        
    def progress(self):
        nloaded = len(self._loaded_data_cache)
        perc = min(int(100*nloaded/self._ndocs), 100)
        bar = pn.indicators.Progress(value=perc, active=self.loading, max=100,
                                    sizing_mode="stretch_width", margin=10, min_width=300)
        
        text = pn.widgets.StaticText(value=f"Loading requested data. {perc}% [{nloaded}/{self._ndocs} documents] done.", 
                                    align="center")
        indicator = pn.indicators.LoadingSpinner(value=self.loading, width=20, height=20)
        cancel = pn.widgets.Button(name="Cancel")
        def cancel_pressed(event):
            self.loading = False
        cancel.on_click(cancel_pressed)
        return CenterColumn(pn.Row(indicator, text), bar, cancel ,sizing_mode="stretch_width",)

    def data_plot(self):
        if self.data_plotter.loading:
            cancel = pn.widgets.Button(name="Cancel")
            def cancel_pressed(event):
                self.loading = False
            cancel.on_click(cancel_pressed)
            progress = self.progress
            content = pn.Column(
                                progress, 
                                cancel, 
                                sizing_mode="stretch_width")

        elif self.data_plotter.data is None:
            load_data = pn.widgets.Button(name="Load data", 
            height=150, button_type="primary")
            load_data.on_click(lambda event: self.load_data())
            content = CenterColumn(load_data)
        else:
            content = self.data_plotter.view
        return content

    def settings(self):
        load_data = pn.widgets.Button(name="Load data", 
           button_type="primary")
        load_data.on_click(lambda event: self.load_data())
        return pn.Column(
            self.filter_tool.settings,
            self.param.partition_size,
            load_data,
            pn.layout.Divider(),
            self.data_plotter.settings,
            width=270,
            sizing_mode="fixed")