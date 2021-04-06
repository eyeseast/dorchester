import click
from click_default_group import DefaultGroup

from . import dotdensity

FORMATS = ("csv", "sqlite", "shapefile", "geojson")


@click.group(cls=DefaultGroup, default="plot")
@click.version_option()
def cli():
    "A toolkit for making dot-density maps in Python"


@cli.command("plot")
@click.argument("source", type=click.Path(exists=True))
@click.argument("dest", type=click.Path(exists=False))
@click.option(
    "-k",
    "--key",
    "keys",
    type=click.STRING,
    multiple=True,
    help="Property name for a population. Use multiple to map different population classes.",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(FORMATS, case_sensitive=False),
    help="Output format. If not given, will guess based on output file extension.",
)
def plot(source, dest, keys, format):
    """
    Generate data for a dot-density map. Input may be any GIS format readable by Fiona (Shapefile, GeoJSON, etc).
    """
