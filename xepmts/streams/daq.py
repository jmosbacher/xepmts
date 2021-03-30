import panel as pn
import param
import numpy as np
import pandas as pd

import httpx
import logging
try:
    import holoviews as hv
    colormaps = hv.plotting.list_cmaps()
    import hvplot.streamz
    import streamz
    from streamz.dataframe import DataFrame as sDataFrame
except:
    colormaps = ["Plasma"]

from concurrent.futures import ThreadPoolExecutor
from panel.io.server import unlocked
from tornado.ioloop import IOLoop


executor = ThreadPoolExecutor(max_workers=5)
logger = logging.getLogger(__name__)


class DAQStreamz(param.Parameterized):
    api_user = param.String()
    api_key = param.String()
    rate_columns = param.List(["array", "signal_channel", "time", "sector","detector",
                          "position_x", "position_y", "rate"], constant=True)
    reader_info_columns = param.List(['time', 'reader', 'host', 'rate',
                                      'status', 'mode', 'buffer_size'], constant=True)
    
    reader_names = param.List(list(range(7)))
    xaxis = param.Selector(["position_x", "sector"], default="position_x")
    yaxis = param.Selector(["position_y", "array"], default="position_y")
    colormap = param.Selector(colormaps, default="Plasma", )
    groupby = param.Selector(["array", "detector"], default="array")
    
    loading = param.Boolean(False, precedence=-1)

    _sources = param.Dict(default=None, precedence=-1)
    _rates = param.Parameter(default=None, precedence=-1)
    _readers = param.Parameter(default=None, precedence=-1)
    
    rates_base_info = param.DataFrame(default=None, precedence=-1)
    readers_base_info = param.DataFrame(default=None, precedence=-1)
    
    def reset_streams(self):
        self._rates = None
        self._readers = None
        self._sources = None
        
    def _fetch_single_reader(self, name):
        try:
            r = httpx.get(f"https://xenonnt.lngs.infn.it/api/getstatus/{name}", 
                    params={'api_user': self.api_user, 'api_key': self.api_key })
            r.raise_for_status()
            resp = r.json()[0]
            rates = resp["channels"]
            result = {}
            result["rates"] = {
                "time": [pd.to_datetime(resp["time"])]*len(rates),  
                "signal_channel": [int(x) for x in rates.keys()],
                "rate": list(rates.values()),
                            }
            result["reader_info"] = {k: [v] for k,v in resp.items() if k in self.reader_info_columns}
            result["reader_info"]["time"] = [pd.to_datetime(t) for t in result["reader_info"]["time"]]
            
        except Exception as e:
            print(e)
            result = {
                "rates": self.rates_example[["time", "signal_channel", "rate"]].to_dict(orient="list"),
                "reader_info": self.reader_info_example.to_dict(orient="list"),
            }
        return result
    
    def emit(self, name, data):
        logger.debug(f"emitting {name}. columns: {data.keys()} ")
        self.sources[name].emit(data)
        
    def data_ready_cb(self, name):
        def cb(future):
            data = future.result()
            self.emit(name, data)
        cb.__name__ = str(name) + "_data_ready"
        return cb

    def all_loaded(self, data):
        self.loading = False
        return data

    @property
    def rates_example(self):
        return pd.DataFrame({col:[] for col in self.rate_columns}).astype({"time":'datetime64[ns]', "signal_channel": 'int64'})
        
    @property
    def reader_info_example(self):
        return pd.DataFrame({col:[] for col in self.reader_info_columns})
    
    @property
    def sources(self):
        if self._sources is None:
            self._sources = {name: streamz.Stream() for name in self.reader_names}
        return self._sources
    
    @property
    def rates(self):
        if self._rates is None:
            rate_streams = [source.pluck("rates").map(pd.DataFrame).filter(lambda df: len(df)>0) for source in self.sources.values()]
            self._rates = streamz.zip(*rate_streams).map(pd.concat).map(self.all_loaded)
        return self._rates
    
    def convert_datetime(self, df):
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
        return df
    
    @property
    def rates_df(self):
        example = self.rates_example
        stream = self.rates
        if self.rates_base_info is not None:
            base = self.rates_base_info.copy()
            example = base.merge(example, how="outer")[self.rate_columns]
            stream = stream.filter(lambda df: len(df)>0).map(lambda df: base.merge(df)).map(lambda df: df[self.rate_columns])
        return sDataFrame(stream, example=example)
            
    @property
    def readers(self):    
        if self._readers is None:
            reader_streams = [source.pluck("reader_info").map(pd.DataFrame) for source in self.sources.values()]
            self._readers = streamz.zip(*reader_streams).map(pd.concat)
        return self._readers
    
    @property
    def readers_df(self):
        example = self.reader_info_example
        stream = self.readers
        if self.readers_base_info is not None:
            base = self.readers_base_info.copy()
            columns = example.columns
            stream = stream.map(lambda df: df.merge(base)[columns])
        return sDataFrame(stream, example=example)
    
    def fetch(self, reader_name, asynchronous=True, timeout=None): 
        if reader_name in self.reader_names:
            f = executor.submit(self._fetch_single_reader, reader_name)
        else:
            raise ValueError(f"No reader named {reader_name} options are: {self.reader_names}")
        if asynchronous:
            loop = IOLoop.current()
            loop.add_future(f, self.data_ready_cb(reader_name))
            return f
        else:
            data = f.result()
            self.emit(reader_name, data)
            
    def fetch_all(self, asynchronous=True, timeout=None):
        futures = {}
        self.loading = True
        for reader, source in self.sources.items():
            f = executor.submit(self._fetch_single_reader, reader)
            futures[reader] = f
            
        if asynchronous:
            loop = IOLoop.current()
            for name, f in futures.items():
                loop.add_future(f, self.data_ready_cb(name))
            return futures
        
        for reader_name, f in futures.items():
            data = f.result(timeout=timeout)
            self.emit(reader_name, data)
    
    
    def rate_plots(self, **kwargs):
        plots = []
        sdf = self.rates_df
        nitems = len(self.rates_base_info)
        psettings = dict(x=self.xaxis,
                        y=self.yaxis,
                        c="rate",
                        s=180,
                        by=self.groupby,
                        subplots=True,
                        cmap=self.colormap,
                        responsive=True,
                        backlog=nitems)
        psettings.update(kwargs)
        return sdf.hvplot.scatter(**psettings)

        groups = self.rates_base_info[self.groupby].unique()
        if len(groups)>1:
            aspect = 1.2
        else:
            aspect = 2
        for group in groups:
            nitems = len(self.rates_base_info[self.rates_base_info[self.groupby]==group])
            plot = sdf[sdf[self.groupby]==group].hvplot.scatter(x=self.xaxis,
                                                                y=self.yaxis,
                                                                c="rate",
                                                                s=180,
                                                                aspect=aspect,
                                                                cmap=self.colormap,
                                                                responsive=True,
                                                                 title=group,
                                                                 backlog=nitems)
            plots.append(plot)
        return hv.NdLayout({group: plot for group,plot in zip(groups, plots)},
                         kdims=self.groupby).cols(2)
        # return pn.layout.GridBox(*plots, ncols=2, sizing_mode="stretch_both")
    
        # bsize = 500
        # initial = None
        # if self.rates_base_info is not None:
        #     bsize = len(self.rates_base_info)
        # return hv.DynamicMap(self._rate_plots,
        #                  streams=[hv.streams.Buffer(self.rates_df, length=bsize)])

    def view(self):
        return pn.panel(self.rate_plots)
    
    def _repr_mimebundle_(self, include=None, exclude=None):
        return self.view()._repr_mimebundle_(include=include, exclude=exclude)
    
    def settings(self):
        parameters = ["xaxis", "yaxis", "groupby"]
        widgets = {}
        return pn.Param(
            self.param,
            parameters=parameters,
            widgets=widgets,
            width=250,
        )
    
class LiveDAQStreamz(DAQStreamz):

    period = param.Number(2000) # milliseconds
    count = param.Integer(default=None)
    timeout = param.Number(default=None) #seconds
    auto_start = param.Boolean(False)

    running = param.Boolean(False, precedence=-1)
    
    _cbs = param.List([], precedence=-1)
    _view = param.Parameter(precedence=-1)
    
    start_button = param.Action(lambda self: self.start(), label="Start")
    stop_button = param.Action(lambda self: self.stop(), label="Stop")
    futures = param.Dict({})

    def callback(self):
        if self.loading:
            return
        if not self.running:
            return
        self.futures = self.fetch_all(asynchronous=True)
                
    def start(self):
        self.stop()  
        cb = pn.state.add_periodic_callback(self.callback, 
                                                period=self.period,
                                                count=self.count,
                                                timeout=self.timeout)
        self._cbs.append(cb)
        self.running = True
        
    def stop(self):
        self.running = False
        for cb in self._cbs:
            if cb.running:
                cb.stop()
        self._cbs = []
        
    @property
    def sources(self):
        if self._sources is None:
            self._sources = super().sources
            if self.auto_start:
                self.start()
        return self._sources
    
    @param.depends("running")
    def controls(self):
        button = pn.widgets.Button(align="center", min_width=100,
                                   sizing_mode="stretch_width")
        if self.running:
            button.name = "Stop"
            button.on_click(lambda event: self.stop())
            return button
            
        else:
            button.name = "Start"
            button.on_click(lambda event: self.start())
            return pn.Row(
                    button,
                    self.param.period,
                    self.param.timeout,
                    self.param.count,
                    align="center",
                    sizing_mode="stretch_width")    

    # @param.depends("running")
    def stream_view(self):
        return self.rate_plots()
        # reader_info = pn.pane.DataFrame(self.readers_df, height=200, sizing_mode="stretch_width")
        # tabs = pn.Tabs(("Rates", self.rate_plots()),
        #             #    ("Reader info", reader_info),
        #                 sizing_mode="stretch_both")
        # if self.running:
        #     return self.rate_plots()
        # else:
        #     return pn.Column("Not running.")
    
    @param.depends("_view",)
    def view(self):
        if self._view is None:
#             rates = pn.pane.DataFrame(self.rates_df, height=500, sizing_mode="stretch_width")
            self._view = pn.Column(self.controls,
                                   self.stream_view(),
                                   height=600,
                                   sizing_mode="stretch_width")
        return self._view
    
    def settings(self):
        parameters = ["period", "count", "timeout"]
        widgets = {}
        params = pn.Param(
            self.param,
            parameters=parameters,
            widgets=widgets,
            expand_button=False,
            width=250,
        )
        return pn.Column(params, 
                         self.daq_stream.settings(),
                         width=250,)
    
    def _repr_mimebundle_(self, include=None, exclude=None):
        return self.view()._repr_mimebundle_(include=include, exclude=exclude)
    
class LiveDAQStreamzViewer(param.Parameterized):
    
    CONFIGS = {
        "tpc": dict(xaxis="position_x", yaxis="position_y", groupby="array", reader_names=[f"reader{i}_reader_0" for i in range(4)]),
        "nveto": dict(xaxis="sector", yaxis="array", groupby="detector", reader_names=["reader6_reader_0", "reader6_reader_1"]),
        "muveto": dict(xaxis="sector", yaxis="array", groupby="detector", reader_names=["reader5_reader_0"]),

    }

    client = param.Parameter(precedence=-1)
    api_user = param.String()
    api_key = param.String()
    detector = param.Selector(list(CONFIGS))
    daq_stream = param.Parameter(precedence=-1)
    daq_streams = param.Dict({})
    add_detector = param.Action(lambda self: self.add_stream(self.detector))
    reload_detector = param.Action(lambda self: self.reload_stream(self.detector))
    loading = param.Boolean(False, precedence=-1)
    
    def add_stream(self, detector):
        if detector not in self.daq_streams:
            self.loading = True
            try:
                streams = self.daq_streams
                config = self.CONFIGS[detector]
                installs = getattr(self.client, detector).installs.to_dataframe()
                installs["signal_channel"] = installs.pmt_index.astype("int64")
                stream = LiveDAQStreamz(name=detector,
                                        api_key=self.api_key,
                                        api_user=self.api_user,
                                        rates_base_info=installs,
                                        **config
                                    )
                streams[detector] = stream
                self.daq_streams = streams
            finally:
                self.loading = False

        self.daq_stream = self.daq_streams[detector]

    def reload_stream(self, detector):
        stream = self.daq_streams.pop(detector, None)
        if stream:
            stream.stop()
        self.add_stream(detector)
        
    @param.depends("daq_stream", "loading")
    def streams_view(self):
        if self.loading:
            return pn.indicators.LoadingSpinner(value=True)
        
        if self.daq_stream is None:
            return pn.Column("## No streams loaded yet")
        
        # streams = pn.Tabs(*[(k, v.view) for k,v in self.daq_streams.items()])
        return self.daq_stream.view()
    
    def controls(self):
        return pn.Row(self.param.detector,
                      self.param.add_detector,
                      self.param.reload_detector,
                     sizing_mode="stretch_width")
    
    
    def view(self):
        return pn.Column(
            self.controls(),
            self.streams_view,
            sizing_mode="stretch_both"
                        )
        
    def _repr_mimebundle_(self, include=None, exclude=None):
        return self.view()._repr_mimebundle_(include=include, exclude=exclude)
    