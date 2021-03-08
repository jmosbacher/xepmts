import panel as pn
import param
import numpy as np
import pandas as pd
import streamz
from streamz.dataframe import DataFrame as sDataFrame
import holoviews as hv
import httpx
import logging

from concurrent.futures import ThreadPoolExecutor
from panel.io.server import unlocked
from tornado.ioloop import IOLoop


executor = ThreadPoolExecutor(max_workers=4)
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
    groupby = param.Selector(["array", "detector"], default="array")
    
    _sources = param.List(default=None, precedence=-1)
    _streams = param.List(default=None, precedence=-1)
    _rates = param.Parameter(default=None, precedence=-1)
    _readers = param.Parameter(default=None, precedence=-1)
    
    rates_base_info = param.DataFrame(default=None, precedence=-1)
    readers_base_info = param.DataFrame(default=None, precedence=-1)
    

    def reset_streams(self):
        self._rates = None
        self._readers = None
        self._streams = None
        self._sources = None
        
    def _fetch_status(self, i):
        try:
            r = httpx.get(f"https://xenonnt.lngs.infn.it/api/getstatus/reader{i}_reader_0", 
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
    
    @property
    def rates_example(self):
        return pd.DataFrame({col:[] for col in self.rate_columns}).astype({"time":'datetime64[ns]', "signal_channel": 'int64'})
        
    
    @property
    def reader_info_example(self):
        return pd.DataFrame({col:[] for col in self.reader_info_columns} )
    
    @property
    def sources(self):
        if self._sources is None:
            self._sources = [streamz.Stream() for _ in self.reader_names]
        return self._sources
    
    @property
    def streams(self):
        if self._streams is None:
            self._streams = [source.map(self._fetch_status) for source in self.sources]
        return self._streams
    
    @property
    def rates(self):
        if self._rates is None:
            rate_streams = [stream.pluck("rates").map(pd.DataFrame) for stream in self.streams]
            self._rates = streamz.zip(*rate_streams).map(pd.concat).map(lambda df: df.infer_objects())
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
            stream = stream.map(lambda df: base.infer_objects().merge(df)).map(lambda df: df[self.rate_columns])
        return sDataFrame(stream, example=example)
            
    @property
    def readers(self):    
        if self._readers is None:
            reader_streams = [stream.pluck("reader_info").map(pd.DataFrame) for stream in self.streams]
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
        for reader, source in zip(self.reader_names, self.sources):
            if reader == reader_name:
                f = executor.submit(source.emit, reader)
                break
        else:
            raise ValueError(f"No reader named {reader_name} options are: {self.reader_names}")
        if asynchronous:
            return f
        else:
            return f.result()
        
    def fetch_all(self, asynchronous=True, timeout=None):
        futures = []
        for reader, source in zip(self.reader_names, self.sources):
            f = executor.submit(source.emit, reader)
            futures.append(f)
        if asynchronous:
            return futures
        for f in futures:
            f.result(timeout=timeout)
        
    def _rate_plots(self, data):
        if not len(data):
            data = self.rates_example
            if self.rates_base_info is not None:
                data =  self.rates_base_info.merge(data, how="outer")
                
        plot = hv.Points(data, kdims=[self.xaxis, self.yaxis],
                             vdims=["rate", "signal_channel", self.groupby ])
        def pick_last(x):
            if len(x):
                return x.iloc[-1]
            else:
                return np.nan
            
        plots = {group: plot.select(**{self.groupby: group}).aggregate([self.xaxis, self.yaxis], pick_last)
                         for group in data[self.groupby].unique()}
        
        if len(plots)>1:
            aspect = 1
        else:
            aspect = 2
        maxval = data["rate"].max() or None
        return hv.NdLayout(plots).cols(2).opts(
            hv.opts.Points(color="rate", aspect=aspect, colorbar=True, 
                  size=15, clim=(1, maxval), logz=True,
                 default_tools=["hover", "tap"], cmap="Plasma")
        )
    
    def rate_plots(self):
        return hv.DynamicMap(self._rate_plots, streams=[hv.streams.Buffer(self.rates_df, length=500)])
    
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
    loading = param.Boolean(False, precedence=-1)
    _cbs = param.List([], precedence=-1)
    _view = param.Parameter(precedence=-1)
    
    start_button = param.Action(lambda self: self.start(), label="Start")
    stop_button = param.Action(lambda self: self.stop(), label="Stop")
    futures = param.List([])

    def wait_for_futures(self):
        self.futures = [f for f in self.futures if f.running()]
        if not self.futures:
            self.loading = False
            self._cbs.pop(-1)
        
    def callback(self):
        if self.loading:
            return
        self.loading = True
        
        self.futures = self.fetch_all(asynchronous=True)
#         self.future = executor.submit(self.wait_for_futures, futures)
        cb = pn.state.add_periodic_callback(self.wait_for_futures, period=100)              
        self._cbs.append(cb)
#         loop = IOLoop.current()
#         for idx in gains.page_numbers:
#             future = executor.submit(gains.get_page, idx)
#             loop.add_future(future, self._update_gains)
            
    def start(self):
        self.stop()  
        cb = pn.state.add_periodic_callback(self.callback, 
                                                period=self.period,
                                                count=self.count,
                                                timeout=self.timeout)
        self._cbs.append(cb)
        self.running = True
        
    def stop(self):
        for cb in self._cbs:
            if cb.running:
                cb.stop()
        self._cbs = []
        self.running = False
        
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
    
    @param.depends("running")
    def stream_view(self):
        reader_info = pn.pane.DataFrame(self.readers_df, height=200, sizing_mode="stretch_width")
        tabs = pn.Tabs(("Rates", self.rate_plots()),
                       ("Reader info", reader_info),
                        sizing_mode="stretch_both")
        return tabs
    
    @param.depends("_view",)
    def view(self):
        if self._view is None:
#             rates = pn.pane.DataFrame(self.rates_df, height=500, sizing_mode="stretch_width")
            self._view = pn.Column(self.controls,
                                   self.stream_view,
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
        "tpc": dict(xaxis="position_x", yaxis="position_y", groupby="array", reader_names=[0,1,2,3,4]),
        "nveto": dict(xaxis="sector", yaxis="array", groupby="detector", reader_names=[6]),
        "muveto": dict(xaxis="sector", yaxis="array", groupby="detector", reader_names=[5]),

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
        if detector in self.daq_streams:
            return
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
            
    def reload_stream(self, detector):
        stream = self.daq_streams.pop(detector, None)
        if stream:
            stream.stop()
        self.add_stream(detector)
        
    @param.depends("daq_streams", "loading")
    def streams_view(self):
        if self.loading:
            return pn.indicators.LoadingSpinner(value=True)
        
        if not len(self.daq_streams):
            return pn.Column("## No streams loaded yet")
        
        streams = pn.Tabs(*[(k, v.view) for k,v in self.daq_streams.items()])
        return streams
    
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
    