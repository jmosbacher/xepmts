
import os
from xepmts.api.utils import read_endpoint_files, resources_from_templates

def get_domain():
    SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
    ENDPOINT_TEMPLATE_DIR = os.path.join(SOURCE_DIR, "endpoint_templates")
    ENDPOINT_DIR = os.getenv("XEPMTS_ENDPOINT_DIR", "")
    if not ENDPOINT_DIR:
        templates = read_endpoint_files(ENDPOINT_TEMPLATE_DIR)
        DOMAIN = resources_from_templates(templates)
    else:
        DOMAIN = read_endpoint_files(ENDPOINT_DIR)
    return DOMAIN