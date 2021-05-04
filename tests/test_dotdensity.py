import csv
import itertools

import geojson
import pytest
from shapely import geometry
from shapely.ops import triangulate

from dorchester.point import Point, Error
from dorchester import dotdensity
from conftest import feature


def test_point_to_geo():
    point = Point(0, 0, "test", 1)
    geom = geometry.shape(point)

    assert isinstance(geom, geometry.Point)
    assert (geom.x, geom.y) == (point.x, point.y)


def test_points_on_triangle():
    triangle = geojson.utils.generate_random("Polygon", 3)
    vertices = triangle.coordinates[0][:3]
    points = dotdensity.points_on_triangle(vertices, 100)

    assert len(points) == 100
    assert all(len(p) == 2 for p in points)


def test_total_area():
    f = feature(0, population=100)
    geom = geometry.shape(f.geometry)
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
    population = f.properties["population"]
    geom = geometry.shape(f.geometry)

    points, err = dotdensity.points_in_shape(geom, population)

    assert len(points) - err == population


def test_plot_total_points(source):
    "Check that we're generating the correct number of points across features"
    fc = geojson.loads(source.read_text())
    population = sum(f.properties["population"] for f in fc.features)

    # sanity checks
    assert 10 == len(fc.features)
    assert 1000 == population

    points, errors = zip(*dotdensity.generate_points(source, "population"))
    points = list(itertools.chain(*points))
    total_err = sum(e.offset for e in errors)

    # because we're fixing now
    assert 0 == total_err
    assert (len(points)) == population


def test_generate_points(source):
    "Check that we return the right data structure"
    gen = dotdensity.generate_points(source, "population")

    points, err = next(gen)
    points = list(points)
    point = points[0]

    assert isinstance(err, Error)
    assert isinstance(err.offset, int)
    assert isinstance(point, dotdensity.Point)
    assert isinstance(point.x, float)
    assert isinstance(point.y, float)

    assert "population" == point.group
    assert "0" == point.fid


def test_points_in_polygons(source):
    "Check that all points are in the correct polygons"
    fc = geojson.loads(source.read_text())

    # group points by fid, check that each is within the corresponding polygon
    features = {f.id: f for f in fc.features}
    for points, err in dotdensity.generate_points(source, "population"):
        for point in points:
            feature = features[int(point.fid)]
            geom = geometry.shape(feature.geometry)
            assert geom.contains(geometry.shape(point))


def test_multi_population(source, feature_collection):
    population = sum(f.properties["population"] for f in feature_collection.features)
    households = sum(f.properties["households"] for f in feature_collection.features)
    ratio = households / population

    points = []
    errors = {"population": 0, "households": 0}

    for p, err in dotdensity.generate_points(source, "population", "households"):
        points.extend(p)
        errors[err.group] += err.offset

    groups = {}
    for group, point_list in itertools.groupby(points, lambda p: p.group):
        groups[group] = list(point_list)

    # errors fixed
    assert errors["population"] == 0
    assert errors["households"] == 0

    assert (
        (len(points) - errors["population"] - errors["households"])
    ) == population + households

    assert (
        len([p for p in points if p.group == "population"]) - errors["population"]
        == population
    )

    assert (
        len([p for p in points if p.group == "households"]) - errors["households"]
        == households
    )


def test_custom_fid():
    f = feature(None, 5, geoid="01", population=100)
    points, err = dotdensity.points_in_feature(f, "population", fid_field="geoid")

    assert "01" == err.fid
    for point in points:
        assert "01" == point.fid


def test_coerce_to_int():
    f = feature(None, 5, geoid="01", population="100")
    points, err = dotdensity.points_in_feature(f, "population", coerce=True)

    assert 100 == (len(list(points)) - err.offset)


def test_missing_field():
    f = feature(1, 5, population=100, cats=None)
    points, err = dotdensity.points_in_feature(f, "households", coerce=True)
    points = list(points)
    assert len(points) == 0

    points, err = dotdensity.points_in_feature(f, "cats", coerce=True)

    assert len(list(points)) == 0
