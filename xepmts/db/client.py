from .endpoints import get_endpoints
import os
import pkg_resources

DEFAULT_SERVER = "xenonnt.org"
SERVERS = {
    "xenonnt.org": "https://api.pmts.xenonnt.org/",
    "gae": "https://api-dot-xenon-pmts.uc.r.appspot.com/",
    "gae_proxy": "https://api-proxy-dot-xenon-pmts.uc.r.appspot.com/",
    "deta": "https://38nq2t.deta.dev/"
}


def get_client(version, scopes=["read:all"], servers=None):
    import eve_panel
    if servers is None:
        servers = {f"{name}": f"{address.strip('/')}/{version}"
                    for name, address in SERVERS.items()}
        servers["default"] = f"{SERVERS[DEFAULT_SERVER].strip('/')}/{version}"
    elif isinstance(servers, str):
        servers = {'default': servers}
    elif isinstance(servers, (tuple,list)):
        servers = {f'server_{i}': server for i,server in enumerate(servers)}
    if not isinstance(servers, dict):
        raise ValueError("Servers parameter must be of type dict with signiture: {name: url}")

    endpoints = get_endpoints(servers.values())
    client = eve_panel.EveClient.from_domain_def(domain_def=endpoints, name="xepmts", auth_scheme="Bearer",
                             sort_by_url=True, servers=servers)
    client.select_server("default")
    client.db = client
    if version=="v2":
        client.set_auth("XenonAuth")
        client.set_credentials(audience="https://api.pmts.xenonnt.org", scopes=scopes)
        
    return client

def default_client():
    return get_client("v2")