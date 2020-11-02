"""Console script for xepmts."""
import sys
import os

import click
from xepmts.api.app import make_local_app
from xepmts.api.utils import resources_from_templates, read_endpoint_files
from xepmts.api.settings import SETTINGS_DIR
from ruamel.yaml import YAML
yaml = YAML()
yaml.indent(mapping=4, sequence=4, offset=2)

DEFAULT_TEMPLATE_DIR = os.path.join(os.path.abspath(SETTINGS_DIR), "endpoint_templates")

@click.group()
def main():
    """Console script for xepmts."""
    return 0

@main.command()
@click.option('--template_dir', default=DEFAULT_TEMPLATE_DIR, help='Template directory')
@click.option('--out', default="./xepmts/api/endpoints", help='Output directory')
def generate_endpoints(template_dir, out):
    
    import eve
    if not os.path.isdir(out):
        os.mkdir(out)
    templates = read_endpoint_files(template_dir)
    domain = resources_from_templates(templates)
    app = eve.Eve(settings={"DOMAIN": domain})
    for k, v in dict(app.config["DOMAIN"]).items():
        fpath = os.path.join(out, k+".yml")
        endpoint = {k: v}
        with open(fpath, "w") as f:
            yaml.dump(endpoint, f)

@main.command()
def serve():
    app = make_local_app()
    app.run(host="localhost", debug=True, ) #ssl_context="adhoc"


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
