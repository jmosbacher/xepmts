
import param
import json
import os

class ConfigParameter(param.Parameter):

    __slots__ = ["env_prefix", "klass"]

    def __init__(self, klass, env_prefix="", **kwargs):
        super().__init__(**kwargs)
        self.env_prefix = env_prefix
        self.klass = klass
       
    def _set_names(self, attrib_name):
        env_name = attrib_name.upper()
        env_name = self.env_prefix.upper() + "_" + env_name
        if os.getenv(env_name, ""):
            env = os.getenv(env_name, "")
            try:
                env = json.loads(env)
            except Exception as e:
                pass
            self.default = self.klass(env)
        super()._set_names(attrib_name)
        
class Config(param.Parameterized):
    API_SERVER = ConfigParameter(str, env_prefix="xepmts", default="https://xestore-dot-xenon-pmts.uc.r.appspot.com/v1")
    AUTH_SERVER_URI = ConfigParameter(str, env_prefix="xepmts", default="https://pmts.xenonnt.org/db_api/jwt/device/")
    API_TOKEN = ConfigParameter(str, env_prefix="xepmts", default="")
    DEBUG = ConfigParameter(bool, env_prefix="xepmts", default=False)
    MAX_LOG_SIZE = 20
    MAX_MESSAGES = 3
    META_FIELDS = ["_version", "_latest_version", "_etag", "_created"]
    GUI_WIDTH = 600


config = Config()
