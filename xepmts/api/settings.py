import os
from xepmts.api.utils import read_endpoint_files, resources_from_templates

from copy import deepcopy
from xepmts.api.secrets import MONGO_PASSWORD


SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ENDPOINT_DIR = os.path.join(SETTINGS_DIR, "endpoints")
ENDPOINT_DIR = os.getenv("XEPMTS_ENDPOINT_DIR", DEFAULT_ENDPOINT_DIR)
DOMAIN = read_endpoint_files(ENDPOINT_DIR)
# DOMAIN = resources_from_templates(domain)

URL_PREFIX = os.getenv("XEPMTS_URL_PREFIX", "")
API_VERSION = "v1"
RESOURCE_METHODS = ["GET", "POST"]
ITEM_METHODS = ["GET", "PUT", "PATCH", "DELETE"]
ALLOWED_READ_ROLES = ["admin", "superuser", "expert", "user", "read", "write"]
ALLOWED_WRITE_ROLES = ["admin", "superuser", "expert", "write"]
EMBEDDING = True
MEDIA_PATH = "files"
PAGINATION_LIMIT = 10000
SCHEMA_ENDPOINT = "schema"
IF_MATCH = True
ENFORCE_IF_MATCH = False
HATEOAS = True
VERSIONS = "_versions"
NORMALIZE_ON_PATCH = False

# ----------------- Mongo config ------------------------------------------#
MONGO1T_HOST = MONGO_HOST = os.getenv("XEPMTS_MONGO_HOST", "localhost") 
MONGO1T_PORT = MONGO_PORT = int(os.getenv("XEPMTS_MONGO_PORT", 27017))
MONGO_DBNAME = os.getenv("XEPMTS_MONGO_DB", "pmts")
MONGO1T_DBNAME = MONGO_DBNAME + "1t"
MONGO1T_AUTH_SOURCE = MONGO_AUTH_SOURCE = os.getenv("XEPMTS_MONGO_AUTH_SOURCE", MONGO_DBNAME)
MONGO1T_PASSWORD = MONGO_PASSWORD
replica_set = os.getenv("XEPMTS_MONGO_REPLICA_SET", "")
if replica_set:
    MONGO1T_REPLICA_SET = MONGO_REPLICA_SET = replica_set
mongo_uri = os.getenv("XEPMTS_MONGO_URI", "")
if mongo_uri:
    MONGO1T_URI = MONGO_URI = mongo_uri
MONGO1T_USERNAME = MONGO_USERNAME = os.getenv("XEPMTS_MONGO_USER", "")

#-------------------------------------------------------------------------#

SERVERS = ["https://api."+os.getenv('XEPMTS_DOMAIN','pmts.xenonnt.org'),]

X_DOMAINS = ['http://localhost:8000',
            'http://127.0.0.1:8000',
            'http://127.0.0.1:5000',
            'http://editor.swagger.io',
            "https://"+os.getenv('XEPMTS_DOMAIN','pmts.xenonnt.org'),
            "https://api."+os.getenv('XEPMTS_DOMAIN','pmts.xenonnt.org'),
            "https://website."+os.getenv('XEPMTS_DOMAIN','pmts.xenonnt.org'),
            "https://panels."+os.getenv('XEPMTS_DOMAIN','pmts.xenonnt.org'),
            "https://catalog."+os.getenv('XEPMTS_DOMAIN','pmts.xenonnt.org'),
             ]

X_HEADERS = ['Content-Type', 'If-Match', 'Authorization', 'X-HTTP-Method-Override']  # Needed for the "Try it out" buttons