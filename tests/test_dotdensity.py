import csv
import itertools

import geojson
import pytest
from shapely.geometry import shape, Point
from shapely.ops import triangulate

from dorchester import dotdensity
from conftest import feature


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
    tolerance = 2  # account for rounding

    population = f.properties["population"]
    geom = shape(f.geometry)
    points = list(itertools.chain(*dotdensity.points_in_shape(geom, population)))

    assert abs(len(points) - population) < tolerance


def test_plot_total_points(source):
    "Check that we're generating the correct number of points across features"
    fc = geojson.loads(source.read_text())
    population = sum(f.properties["population"] for f in fc.features)
    tolerance = 3  # account for rounding

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
    for point in points:
        feature = features[int(point.fid)]
        geom = shape(feature.geometry)
        assert geom.contains(Point(point.x, point.y))


def test_multi_population(source, feature_collection):
    population = sum(f.properties["population"] for f in feature_collection.features)
    households = sum(f.properties["households"] for f in feature_collection.features)
    ratio = households / population
    tolerance = 3
    points = sorted(
        dotdensity.points(source, "population", "households"), key=lambda p: p.group
    )

    groups = {}
    for group, point_list in itertools.groupby(points, lambda p: p.group):
        groups[group] = list(point_list)

    assert abs(len(points) - (population + households)) < tolerance
    assert round(len(groups["households"]) / len(groups["population"]), 2) == round(
        ratio, 2
    )


def test_plot_csv(source, tmpdir):
    "Try the whole thing here"
    dest = tmpdir / "output.csv"
    fc = geojson.loads(source.read_text())
    population = sum(f.properties["population"] for f in fc.features)
    tolerance = 3  # again, rounding

    dotdensity.plot(source, dest, ["population"])

    with dest.open() as d:
        rows = list(csv.DictReader(d))

    assert abs(len(rows) - population) < tolerance
