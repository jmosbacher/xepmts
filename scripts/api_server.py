import os
import xepmts
from xepmts.api.app import make_app

settings_file = os.path.abspath(xepmts.api.settings)
app = make_app(settings_file, auth=None, swagger=True, swagger_ui=True)

if __name__ == '__main__':
    app = make_app(settings_file, auth=None, swagger=True, swagger_ui=True)
    app.run(host="localhost", debug=True, ) #ssl_context="adhoc"
    