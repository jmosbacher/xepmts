
import os

ENDPOINT_DIR = os.getenv("XEPMTS_ENDPOINT_DIR", "")
if not os.path.isabs(ENDPOINT_DIR):
    SOURCE_PATH = os.path.realpath(os.path.dirname(__file__))
    os.environ["XEPMTS_ENDPOINT_DIR"] = os.path.join(SOURCE_PATH, "endpoints")

import xepmts
from xepmts.api.app import make_app
from xepmts.api.auth import XenonTokenAuth
from xepmts.api.settings import get_settings_dict
from eve_jwt import JWTAuth

settings = get_settings_dict()
app = make_app(settings=settings, auth=JWTAuth, swagger=True, swagger_ui=True)

if __name__ == '__main__':
    app.run(host="localhost", debug=True, ) #ssl_context="adhoc"
    