import logging
import geojson
import pytest
import shapely


def feature(id=None, vertices=5, **properties):
    "Generate a random feature"
    geometry = geojson.utils.generate_random("Polygon", vertices)
    return geojson.Feature(id, geometry, properties)


@pytest.fixture()
def feature_collection():
    features = (
        feature(i, population=100, households=20, cats="5", geoid=f"{i:03}")
        for i in range(10)
    )
    features = [f for f in features if is_valid(f.geometry)]
    return geojson.FeatureCollection(features)


@pytest.fixture()
def source(tmp_path, feature_collection):
    path = tmp_path / "fc.geojson"
    with path.open("w") as f:
        geojson.dump(feature_collection, f)

    return path


def is_valid(geom):
    return shapely.geometry.shape(geom).is_valid
