
import pathlib
import os
from xepmts.api.server.v1.utils import read_endpoint_files, resources_from_templates
from xepmts import api

SOURCE_DIR = pathlib.Path(__file__).parent.parent.parent
DEFAULT_TEMPLATE_DIR = SOURCE_DIR / "endpoints"

def get_domain():
    ENDPOINT_TEMPLATE_DIR = os.getenv("XEPMTS_ENDPOINT_TEMPLATE_DIR", DEFAULT_TEMPLATE_DIR.absolute())
    # print(ENDPOINT_TEMPLATE_DIR)
    ENDPOINT_DIR = os.getenv("XEPMTS_ENDPOINT_DIR", "")
    if not ENDPOINT_DIR:
        templates = read_endpoint_files(ENDPOINT_TEMPLATE_DIR)
        DOMAIN = resources_from_templates(templates)
    else:
        DOMAIN = read_endpoint_files(ENDPOINT_DIR)
    return DOMAIN