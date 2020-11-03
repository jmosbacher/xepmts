
import xepmts
from app import make_app
from xepmts.api.auth import XenonTokenAuth
from xepmts.api.settings import get_settings_dict

settings = get_settings_dict()
app = make_app(settings=settings, auth=XenonTokenAuth, swagger=True, swagger_ui=True)

if __name__ == '__main__':
    app.run(host="localhost", debug=True,) #ssl_context="adhoc"
    