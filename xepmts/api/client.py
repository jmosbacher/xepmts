from xepmts.api import server
import os
import pkg_resources

DEFAULT_SERVER = "gae_proxy"
SERVERS = {
    "xenon": "https://api.pmts.xenonnt.org/",
    "gae": "https://api-dot-xenon-pmts.uc.r.appspot.com/",
    "gae_proxy": "https://api-proxy-dot-xenon-pmts.uc.r.appspot.com/",
    "deta": "https://38nq2t.deta.dev/"
}

def get_client(version):
    import eve_panel
    servers = {f"{name}_{version}": f"{address.strip('/')}/{version}"
                for name, address in SERVERS.items()}
    servers["default"] = f"{SERVERS[DEFAULT_SERVER].strip('/')}/{version}"

    make_app = getattr(server, version).app.make_app
    app = make_app()
    client = eve_panel.EveClient.from_app(app, name="xepmts", auth_scheme="Bearer",
                             sort_by_url=True, servers=servers)
    client.select_server("default")
    client.db = client
    if version=="v2":
        client.set_auth("XenonAuth")
        client.set_credentials(audience="https://api.pmts.xenonnt.org", scopes=["read:all"])
        
    return client

def default_client():
    return get_client("v1")