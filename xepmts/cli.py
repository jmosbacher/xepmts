"""Console script for xepmts."""
import sys
import os

import click
from xepmts.api.utils import resources_from_templates, read_endpoint_files
from xepmts.api.domain import DEFAULT_TEMPLATE_DIR
from ruamel.yaml import YAML
yaml = YAML()
yaml.indent(mapping=4, sequence=4, offset=2)


@click.group()
def main():
    """Console script for xepmts."""
    return 0

@main.command()
@click.option('--template_dir', default=DEFAULT_TEMPLATE_DIR, help='Template directory')
@click.option('--out', default="./api_server/endpoints", help='Output directory')
def generate_endpoints(template_dir, out):
    # import eve
    if not os.path.isdir(out):
        os.makedirs(out)
    templates = read_endpoint_files(template_dir)
    domain = resources_from_templates(templates)
    for k, v in domain.items():
        if "url" in v:
            rpath, _, fname = v["url"].rpartition("/")
            abspath = os.path.join(out, rpath)
            if not os.path.exists(abspath):
                os.makedirs(abspath)
        else:
            fname = k
            abspath = out
        fpath = os.path.join(abspath, fname+".yml")
        endpoint = {k: v}
        with open(fpath, "w") as f:
            yaml.dump(endpoint, f)

@main.command()
def serve():
    from xepmts.api.app import make_local_app
    app = make_local_app()
    app.run(host="localhost", debug=True, ) #ssl_context="adhoc"


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
