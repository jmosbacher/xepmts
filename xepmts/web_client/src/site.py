# pylint: disable=redefined-outer-name,protected-access,missing-function-docstring
"""In this module we provide functionality to serve the Site

We provide some basic settings for `panel.serve` below. They might need tweeking to support your
use case.

For more info refer to the [README](README.md) and the section on Deployment.
"""
import os
import platform



from xepmts.web_client.src.shared import config, modifications
modifications.apply()

import holoviews as hv
hv.extension("bokeh")

import panel as pn
import xepmts

xepmts.extension()

def serve(**kwargs):
    """Serves the site

    Use the configuration files together with the
    [BOKEH environment variables]\
    (https://docs.bokeh.org/en/latest/docs/reference/settings.html#bokeh-settings) to configure
    your site and how its served.
    """
    address = os.getenv("BOKEH_ADDRESS", "localhost")
    if platform.system() == "Windows":
        kwargs.pop("num_procs")
    
    pn.serve(
            config.routes,
            port=kwargs.get("port", 5006),
            dev=kwargs.get("debug", False),
            title=config.site_name,
            address=kwargs.get("address", address),
            num_procs=kwargs.get("nproc", 1),
            static_dirs=config.static_dirs,
            allow_websocket_origin=kwargs.get("allow_websocket_origin", ["localhost"]),

        )


if __name__ == "__main__":
    serve()
