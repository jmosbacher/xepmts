from xepmts.api import server
import os
import pkg_resources


def make_client(version):
    import eve_panel

    make_app = getattr(server, version).app.make_app
    app = make_app()
    client = eve_panel.EveClient.from_app(app, name="xepmts", sort_by_url=True)
    client._http_client.auth.set_auth_by_name("Bearer")
    client.db = client
    return client

def default_client():
    return make_client("v1")