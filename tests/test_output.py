import csv
import geojson
import pytest

from dorchester.dotdensity import Point
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
        row == point._asdict()


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
