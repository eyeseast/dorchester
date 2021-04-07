import itertools
import random

import geojson
import pytest
from click.testing import CliRunner
from shapely.geometry import shape
from shapely.ops import triangulate

from dorchester.cli import cli
from dorchester import dotdensity


def feature(id=None, vertices=5, **properties):
    "Generate a random feature"
    geometry = geojson.utils.generate_random("Polygon", vertices)
    return geojson.Feature(id, geometry, properties)


@pytest.fixture
def feature_collection():
    features = [feature(i, population=100, households=20) for i in range(10)]
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


def test_points_on_triangle():
    triangle = geojson.utils.generate_random("Polygon", 3)
    vertices = triangle.coordinates[0][:3]
    points = dotdensity.points_on_triangle(vertices, 100)

    assert len(points) == 100
    assert all(len(p) == 2 for p in points)


def test_total_area():
    f = feature(0, population=100)
    geom = shape(f.geometry)
    triangles = [t for t in triangulate(geom) if t.within(geom)]
    ratios = [t.area / geom.area for t in triangles]
    counts = [r * f.properties["population"] for r in ratios]

    # account for floats
    tolerance = 0.0001

    # should match
    assert geom.area == sum(t.area for t in triangles)

    # make sure we get close
    assert 1 - sum(ratios) < tolerance

    # should add up
    assert abs(sum(counts) - f.properties["population"]) < tolerance


def test_points_in_shape():
    f = feature(0, 8, population=100)
    tolerance = 2

    population = f.properties["population"]
    geom = shape(f.geometry)
    points = list(itertools.chain(*dotdensity.points_in_shape(geom, population)))

    assert abs(len(points) - population) < tolerance


def test_plot_total_points(source):
    "Check that we're generating the correct number of points across features"
    fc = geojson.loads(source.read_text())
    population = sum(f.properties["population"] for f in fc.features)
    tolerance = 5

    # sanity checks
    assert 10 == len(fc.features)
    assert 1000 == population

    points = list(dotdensity.points(source, "population"))

    assert abs(len(points) - population) < tolerance


def test_generate_points(source):
    "Check that we return the right data structure"
    points = dotdensity.points(source, "population")

    point = next(points)

    assert isinstance(point, dotdensity.Point)
    assert isinstance(point.x, float)
    assert isinstance(point.y, float)

    assert "population" == point.group
    assert "0" == point.fid


def test_points_in_polygons(source):
    "Check that all points are in the correct polygons"
    fc = geojson.loads(source.read_text())
    points = dotdensity.points(source, "population")

    # group points by fid, check that each is within the corresponding polygon
    features = {f.id: f for f in fc.features}
