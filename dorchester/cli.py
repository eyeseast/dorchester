import logging
from pathlib import Path

import click
import fiona

from click_default_group import DefaultGroup
from tqdm import tqdm

from . import dotdensity
from .dotdensity import get_feature_id
from .output import FILE_TYPES, FORMATS

log = logging.getLogger("dorchester")


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
    type=click.Choice(FORMATS.keys(), case_sensitive=False),
    help="Output format. If not given, will guess based on output file extension.",
)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(["w", "a", "x"]),
    default="w",
    show_default=True,
    help="File mode for destination",
)
@click.option(
    "--fid",
    "fid_field",
    type=click.STRING,
    help="Use a property key (instead of feature.id) to uniquely identify each feature",
    default=None,
)
@click.option(
    "--coerce",
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="Coerce properties passed in --key to integers. BE CAREFUL. This could cause incorrect results if misused.",
)
@click.option(
    "--progress",
    type=click.BOOL,
    is_flag=True,
    default=False,
    show_default=True,
    help="Show a progress bar",
)
@click.option(
    "-c",
    "--count",
    type=click.INT,
    help="Feature count, used with progress bar.",
)
@click.option(
    "-m",
    "--multiprocessing",
    "mp",
    is_flag=True,
    default=False,
    help="Use multiprocessing",
)
@click.option("--log", "logfile", type=click.Path(dir_okay=False))
def plot(
    source, dest, keys, format, mode, fid_field, coerce, progress, count, mp, logfile
):
    """
    Generate data for a dot-density map. Input may be any GIS format readable by Fiona (Shapefile, GeoJSON, etc).
    """
    if logfile:
        handler = logging.FileHandler(logfile, "w", "utf-8")
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s: %(message)s")
        handler.setFormatter(formatter)
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)

    source = Path(source)
    dest = Path(dest)

    if format in FORMATS:
        Writer = FORMATS[format]

    else:
        Writer = FILE_TYPES.get(dest.suffix, None)

    if Writer is None:
        raise click.UsageError(f"Unknown file type: {dest.name}")

    if mp:
        generate_points = dotdensity.generate_points_mp
    else:
        generate_points = dotdensity.generate_points

    generator = generate_points(source, *keys, fid_field=fid_field, coerce=coerce)
    if progress:
        count = count or get_feature_count(source)
        click.echo(f"{count} features")
        generator = tqdm(generator, total=count, unit="features")

    log.debug(f"Source: {source}")
    with Writer(dest, mode) as writer:
        if not progress:
            click.echo("Generating points ...")

        for points in generator:
            writer.write_all(points)


# for progress bars
def get_feature_count(source):
    click.echo(f"Counting features in {source}")
    with fiona.open(source) as fc:
        return len(fc)


if __name__ == "__main__":
    cli()
