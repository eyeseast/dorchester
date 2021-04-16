import geojson
import pytest


def feature(id=None, vertices=5, **properties):
    "Generate a random feature"
    geometry = geojson.utils.generate_random("Polygon", vertices)
    return geojson.Feature(id, geometry, properties)


@pytest.fixture()
def feature_collection():
    features = [
        feature(i, population=100, households=20, geoid=f"{i:03}") for i in range(10)
    ]
    return geojson.FeatureCollection(features)


@pytest.fixture()
def source(tmp_path, feature_collection):
    path = tmp_path / "fc.geojson"
    with path.open("w") as f:
        geojson.dump(feature_collection, f)

    return path
