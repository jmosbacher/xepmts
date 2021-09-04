import httpx
import logging


log = logging.getLogger(__name__)

def clean_nones(d):
    return {k:v for k,v in d.items() if v is not None}

def get_endpoints(url, timeout=25, client=None):
    if client is None:
        client = httpx.Client()
    log.info(f"Attempting to read endpoints from {url}")
    r = client.get(url, timeout=timeout)
    if not r.is_error:
        log.info('Endpoints read succesfully from server.')
        return {k: clean_nones(v) for k,v in r.json().items()}
    
def default_endpoints():
    import xepmts_endpoints
    return xepmts_endpoints.get_endpoints()
