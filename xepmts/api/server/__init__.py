from . import v1
from . import v2

VERSIONS = {
    "v1": v1,
    "v2": v2,
}

def get_server(version, **kwargs):
    app =VERSIONS[version].app.make_app(**kwargs)
    return app

def default_server():
    return get_server("v1")