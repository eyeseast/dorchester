import csv
import itertools

import geojson
import pytest
import numpy as np
from shapely import geometry
from shapely.ops import triangulate

from dorchester.point import Point
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

    points = dotdensity.points_in_shape(geom, population)

    assert len(points) == population


def test_plot_total_points(source):
    "Check that we're generating the correct number of points across features"
    fc = geojson.loads(source.read_text())
    population = sum(f.properties["population"] for f in fc.features)

    points = dotdensity.generate_points(source, "population")
    points = list(itertools.chain(*points))

    assert len(points) == population


def test_generate_points(source):
    "Check that we return the right data structure"
    gen = dotdensity.generate_points(source, "population")

    points = next(gen)
    points = list(points)
    point = points[0]

    assert isinstance(point, dotdensity.Point)
    assert isinstance(point.x, float)
    assert isinstance(point.y, float)

    assert "population" == point.group
    assert "0" == point.fid


def test_generate_points_mp(source):
    "Check that we return the right data structure with multiprocessing"
    gen = dotdensity.generate_points_mp(source, "population")

    points = next(gen)
    # points = list(points)
    point = points[0]

    assert isinstance(point, dotdensity.Point)
    assert isinstance(point.x, float)
    assert isinstance(point.y, float)

    assert "population" == point.group


def test_points_in_polygons(source):
    "Check that all points are in the correct polygons"
    fc = geojson.loads(source.read_text())

    # group points by fid, check that each is within the corresponding polygon
    features = {f.id: f for f in fc.features}
    for points in dotdensity.generate_points(source, "population"):
        for point in points:
            feature = features[int(point.fid)]
            geom = geometry.shape(feature.geometry)
            assert geom.contains(geometry.shape(point))


def test_multi_population(source, feature_collection):
    population = sum(f.properties["population"] for f in feature_collection.features)
    households = sum(f.properties["households"] for f in feature_collection.features)
    ratio = households / population

    points = list(
        itertools.chain(*dotdensity.generate_points(source, "population", "households"))
    )

    groups = regroup(points, lambda p: p.group)

    assert len(points) == population + households
    assert len(groups["population"]) == population
    assert len(groups["households"]) == households


def test_custom_fid():
    f = feature(None, 5, geoid="01", population=100)
    points = dotdensity.points_in_feature(f, ["population"], fid_field="geoid")

    for point in points:
        assert "01" == point.fid


def test_coerce_to_int():
    f = feature(None, 5, geoid="01", population="100")
    points = dotdensity.points_in_feature(f, ["population"], coerce=True)

    assert 100 == len(list(points))


def test_distribute_points():
    groups = {"red": 44, "blue": 33, "green": 23}
    points = dotdensity.distribute_points(np.random.rand(100, 2), groups, 0)
    points = sorted(points, key=lambda p: p.group)

    assert len(points) == sum(groups.values())

    for key, group in itertools.groupby(points, lambda p: p.group):
        group = list(group)
        assert len(group) == groups[key]


def test_missing_field():
    f = feature(1, 5, population=100, cats=None)
    points = dotdensity.points_in_feature(f, ["households"], coerce=True)
    points = list(points)
    assert len(points) == 0

    points = dotdensity.points_in_feature(f, ["cats"], coerce=True)

    assert len(list(points)) == 0


def regroup(iterable, key):
    groups = {}
    iterable = sorted(iterable, key=key)
    for key, group in itertools.groupby(iterable, key):
        groups[key] = list(group)
    return groups
