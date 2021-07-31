from typing import Type
import os
import pkg_resources
import logging
from .endpoints import get_endpoints, default_endpoints



log = logging.getLogger(__name__)

SERVERS = {
    "xenonnt.org": "https://api.pmts.xenonnt.org/",
    "gae": "https://api-dot-xenon-pmts.uc.r.appspot.com/",
    "gae_proxy": "https://api-proxy-dot-xenon-pmts.uc.r.appspot.com/",
    "deta": "https://38nq2t.deta.dev/",
    "lngs": "https://xe1t-mysql.lngs.infn.it/api/",
}

DEFAULT_SERVER = "lngs"

def get_client(version, scopes=["read:all"], server='default', extra_servers=None, endpoint_path='endpoints', timeout=25):
    import eve_panel
    servers = {"default": f"{SERVERS[DEFAULT_SERVER].strip('/')}/{version}"}
    servers.update({f"{name}": f"{address.strip('/')}/{version}"
                    for name, address in SERVERS.items()})

    if extra_servers is not None:
        if isinstance(extra_servers, dict):
            servers.update(extra_servers)
        else:
            raise TypeError("extra_servers must be a dictionary of with signiture: {name: url}")
    
    if server in servers:
        url = "/".join([servers[server].rstrip('/'), endpoint_path.lstrip('/')])
        endpoints = get_endpoints(url, timeout=timeout)
    if endpoints is None:
        log.error("Failed to read endpoint definitions from server, loading defaults.")
        endpoints = default_endpoints()
    client = eve_panel.EveClient.from_domain_def(domain_def=endpoints, name="xepmts", auth_scheme="Bearer",
                                sort_by_url=True, servers=servers)
    client.select_server(server)
    client.db = client
    if version=="v2":
        client.set_auth("XenonAuth")
        client.set_credentials(audience="https://api.pmts.xenonnt.org", scopes=scopes)
        
    return client

def default_client():
    return get_client("v2")

def get_admin_client(servers=None):
    import eve_panel
    scopes = ['admin']
    version = 'admin'

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

    client.set_auth("XenonAuth")
    client.set_credentials(audience="https://api.pmts.xenonnt.org", scopes=scopes)
    return client