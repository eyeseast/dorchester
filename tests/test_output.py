import csv
import pathlib

import geojson
import pytest

from dorchester import dotdensity
from dorchester.point import Point, Error
from dorchester.output import CSVWriter, GeoJSONWriter


@pytest.fixture
def points():
    return [Point(i, i, i, i) for i in range(100)]


def test_write_csv(points, tmpdir):
    path = tmpdir / "points.csv"

    with CSVWriter(path, "w") as writer:
        for point in points:
            writer.write(point)

    reader = csv.DictReader(path.open("r"))

    for row, point in zip(reader, points):
        row == point._asdict()


def test_write_many_csv(points, tmpdir):
    path = tmpdir / "points.csv"

    with CSVWriter(path, "w") as writer:
        writer.write_all(points)

    reader = csv.DictReader(path.open("r"))

    for row, point in zip(reader, points):
        for field in point._fields:
            # csv makes everything a string
            assert row[field] == str(getattr(point, field))


def test_append_csv(points, tmpdir):
    path = tmpdir / "points.csv"

    with CSVWriter(path, "w") as writer:
        writer.write_all(points)

    # now, write again, but append
    with CSVWriter(path, "a") as writer:
        writer.write_all(points)

    rows = list(csv.DictReader(path.open("r")))

    assert len(rows) == len(points) * 2


def test_write_geojson(points, tmpdir):
    path = tmpdir / "points.json"

    with GeoJSONWriter(path) as writer:
        writer.write_all(points)

    features = [geojson.loads(line) for line in path.open()]

    assert len(features) == len(points)

    for point, feature in zip(points, features):
        assert [point.x, point.y] == feature.geometry.coordinates
        assert point.group == feature.properties["group"]
        assert point.fid == feature.properties["fid"]


def test_error_path():
    writer = CSVWriter("points.csv")
    assert isinstance(writer.error_path, pathlib.Path)
    assert str(writer.error_path) == "points.errors.csv"


def test_write_errors(tmpdir, source):
    path = tmpdir / "points.csv"
    error_path = tmpdir / "points.errors.csv"

    points = []
    errors = []

    with CSVWriter(path) as writer:
        for p, error in dotdensity.generate_points(source, "population"):
            p_list = list(p)
            points.extend(p_list)
            errors.append(error)
            writer.write_all(p_list)
            writer.write_error(error)

    written_points = list(csv.DictReader(path.open()))
    written_errors = list(csv.DictReader(error_path.open()))

    assert len(points) == len(written_points)
    assert len(errors) == len(written_errors)
