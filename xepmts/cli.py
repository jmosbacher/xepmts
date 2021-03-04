"""Console script for xepmts."""
import sys
import os

import click
import xepmts


@click.group()
def main():
    """Console script for xepmts."""
    return 0


@main.group()
def server():
    pass

@server.command()
@click.option('--address', default="localhost", help='Server address.')
@click.option('--port', default=5006, help='Server port.')
@click.option('--debug', default=False, help='Enable debugging.', is_flag=True)
@click.option('--reload', default=False, help='Enable auto-reload on code change.', is_flag=True)
@click.option('--evalex', default=False, help='Enable Evalex.', is_flag=True)
def serve(address, port, debug, reload, evalex):
    from xepmts.api.server import run_simple
    run_simple(address, port,  debug, reload, evalex)
   
@main.group()
def webclient():
    pass

@webclient.command()
@click.option('--address', default="localhost", help='Server address.')
@click.option('--port', default=5006, help='Server port.')
@click.option('--nproc', default=1, help='Number of Processes to spawn.')
@click.option('--allow_websocket_origin', default=["localhost"],  multiple=True, help='Whitelisted origins for ws connections.')
@click.option('--debug', default=False, help='Enable auto-reload on code change.', is_flag=True)
def serve(address, port, nproc,
          allow_websocket_origin, debug):
    origins = []
    for origin in allow_websocket_origin:
        origin = origin.strip("/")
        # if not origin.startswith("http"):
        #     origin = "http://" + origin
        if not origin.endswith(str(port)):
            origin = origin + f":{port}"
        origins.append(origin)
    from xepmts.web_client.src import site
    site.serve(address=address, port=port, nproc=nproc,
              allow_websocket_origin=origins, debug=debug)
    


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
