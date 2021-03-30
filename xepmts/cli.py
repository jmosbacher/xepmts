"""Console script for xepmts."""
import sys
import os

import click
import xepmts


@click.group()
def main():
    """Console script for xepmts."""
    return 0

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
