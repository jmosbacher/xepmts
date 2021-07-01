import httpx
import xepmts_endpoints

def get_endpoints(servers, endpoint_path='endpoints'):
    for server in servers:
        uri = "/".join([server.rstrip('/'), endpoint_path.lstrip('/')])
        print(f"Attempting to read endpoints from {uri}")
        r = httpx.get(uri)
        if not r.is_error:
            return r.json()
    print("Failed to read endpoint definitions from server, loading defaults.")
    return xepmts_endpoints.get_endpoints()