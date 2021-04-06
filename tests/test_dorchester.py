import pytest
import geojson
from click.testing import CliRunner

from dorchester.cli import cli
from dorchester import dotdensity


def feature(id, **properties):
    "Generate a random feature"
    geometry = geojson.utils.generate_random("Polygon")
    return geojson.Feature(id, geometry, properties)


@pytest.fixture
def feature_collection():
    features = [feature(i, population=100) for i in range(10)]
    return geojson.FeatureCollection(features)


@pytest.fixture()
def source(tmp_path, feature_collection):
    path = tmp_path / "fc.geojson"
    with path.open("w") as f:
        geojson.dump(feature_collection, f)

    return path


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")


def test_plot_total_points(source):

    fc = geojson.loads(source.read_text())
    population = sum(f.properties["population"] for f in fc.features)

    # sanity checks
    assert 10 == len(fc.features)
    assert 1000 == population

    points = list(dotdensity.points(source, "population"))

    assert len(points) == population