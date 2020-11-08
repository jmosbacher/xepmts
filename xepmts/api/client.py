import eve_panel
from xepmts.api.app import make_local_app
import os
import pkg_resources

APPS = {
    entry_point.name: entry_point.load()
    for entry_point
    in pkg_resources.iter_entry_points('xepmts.apps')
}

APPS["db"] =  make_local_app

def make_client(app_names=None):
    if app_names is None:
        app_names = list(APPS)
    apps = {name: APPS[name]() for name in app_names}
    
    client = eve_panel.EveClient.from_apps_dict(apps, name="xepmts", sort_by_url=True)
    for name in apps:
        getattr(client, name)._http_client.auth.set_auth_by_name("Bearer")
    return client

def default_client():
    return make_client()