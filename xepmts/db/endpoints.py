import httpx
import logging
import xepmts_endpoints
from xepmts_endpoints import endpoints


log = logging.getLogger(__name__)

def clean_nones(d):
    return {k:v for k,v in d.items() if v is not None}

def get_endpoints(servers, endpoint_path='endpoints'):
    for server in servers:
        uri = "/".join([server.rstrip('/'), endpoint_path.lstrip('/')])
        log.info(f"Attempting to read endpoints from {uri}")
        try:
            r = httpx.get(uri, timeout=5)
            if not r.is_error:
                log.info('Endpoints read succesfully from server.')
                return {k: clean_nones(v) for k,v in r.json().items()}
        except:
            pass
    log.error("Failed to read endpoint definitions from server, loading defaults.")
    return xepmts_endpoints.get_endpoints()