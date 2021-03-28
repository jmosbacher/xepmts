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


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
