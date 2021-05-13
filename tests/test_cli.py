import csv
import json
import itertools
from pathlib import Path

import fiona
from click.testing import CliRunner
from dorchester.cli import cli

SUFFOLK = Path(__file__).parent / "data" / "suffolk.geojson"


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")


def test_plot(tmpdir, source, feature_collection):
    dest = tmpdir / "output.csv"
    population = sum(f.properties["population"] for f in feature_collection.features)
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["plot", str(source), str(dest), "--key", "population"]
        )

        assert result.exit_code == 0
        assert dest.exists()

        points = list(csv.DictReader(dest.open()))

        assert len(points) == population


def test_plot_geojson(tmpdir, source, feature_collection):
    dest = tmpdir / "output.json"
    population = sum(f.properties["population"] for f in feature_collection.features)
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["plot", str(source), str(dest), "--key", "population"]
        )

        assert result.exit_code == 0
        assert dest.exists()

        points = list(decode_json_newlines(dest.open()))

        assert len(points) == population


def test_custom_fid(tmpdir, source, feature_collection):
    dest = tmpdir / "output.csv"
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["plot", str(source), str(dest), "--key", "population", "--fid", "geoid"],
        )

        assert result.exit_code == 0
        assert dest.exists()

    reader = csv.DictReader(dest.open())
    reader = sorted(reader, key=lambda row: row["fid"])
    groups = {
        fid: list(points)
        for fid, points in itertools.groupby(reader, lambda row: row["fid"])
    }

    for feature in feature_collection.features:
        assert feature.properties["geoid"] in groups


def test_coerce_ints(tmpdir, source, feature_collection):
    dest = tmpdir / "output.csv"
    cats = sum(int(f.properties["cats"]) for f in feature_collection.features)
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["plot", str(source), str(dest), "--key", "cats", "--coerce"],
        )

        assert result.exit_code == 0
        assert dest.exists()

        points = list(csv.DictReader(dest.open()))

        assert len(points) == cats


def test_suffolk_county(tmpdir):
    dest = tmpdir / "suffolk.csv"
    runner = CliRunner()

    with fiona.open(SUFFOLK) as fc:
        total_features = len(fc)
        population = sum(f["properties"]["POP10"] for f in fc)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "plot",
                str(SUFFOLK),
                str(dest),
                "--key",
                "POP10",
                "--fid",
                "BLOCKID10",
            ],
        )

        assert result.exit_code == 0
        assert dest.exists()

        points = list(csv.DictReader(dest.open()))

        assert len(points) == population


def test_suffolk_county_mp(tmpdir):
    dest = tmpdir / "suffolk.csv"
    runner = CliRunner()

    with fiona.open(SUFFOLK) as fc:
        total_features = len(fc)
        population = sum(f["properties"]["POP10"] for f in fc)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "plot",
                str(SUFFOLK),
                str(dest),
                "--key",
                "POP10",
                "--fid",
                "BLOCKID10",
                "--multiprocessing",
            ],
        )

        assert result.exit_code == 0
        assert dest.exists()

        points = list(csv.DictReader(dest.open()))

        assert len(points) == population


def decode_json_newlines(file):
    for line in file:
        yield json.loads(line.strip())
