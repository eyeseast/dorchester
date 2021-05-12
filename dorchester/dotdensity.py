"""
The functions in this module outline the main API for creating the data behind dot density maps.
"""
import itertools
import random

import fiona
import numpy as np
from shapely.geometry import shape
from shapely.ops import triangulate

from .point import Point


def generate_points(src, *keys, fid_field=None, coerce=False):
    """
    Generate dot-density data, reading from source and yielding points.
    Any keys given will be used to extract population properties from features.

    For each feature, yield a generator of Point objects
    """
    with fiona.open(src) as source:
        for feature in source:
            yield points_in_feature(feature, keys, fid_field=fid_field, coerce=coerce)


def points_in_feature(feature, keys, fid_field=None, coerce=False):
    """
    Take a geojson *feature*, create a shape
    Get population from feature.properties using *key*
    Concatenate all points yielded from points_in_shape
    return a list of Point objects
    """
    if fid_field is not None:
        fid = feature["properties"].get(fid_field)
    else:
        fid = feature.get("id")

    geom = shape(feature["geometry"])
    groups = {key: feature["properties"].get(key) or 0 for key in keys}
    if coerce:
        for key, population in groups.items():
            # let this fail if it fails
            groups[key] = int(population)

    # get a total
    population = sum(groups.values())

    points = points_in_shape(geom, population)
    return distribute_points(points, groups, fid)


def points_in_shape(geom, population):
    """
    plot n points randomly within a shapely geom
    first, cut the shape into triangles
    then, give each triangle a portion of points based on relative area
    within each triangle, distribute points using a weighted average
    return a list of (x, y) coordinates
    """
    triangles = [t for t in triangulate(geom) if t.within(geom)]
    points = []
    offset = -1 * population  # count up as we go
    for triangle in triangles:
        ratio = triangle.area / geom.area
        n = round(ratio * population)
        offset += n
        vertices = triangle.exterior.coords[:3]
        if n > 0:
            points.extend(points_on_triangle(vertices, n))

    # too many points
    if offset > 0:
        return points[:-offset]

    # not enough, cycle through triangles until we do
    triangles = itertools.cycle(triangles)
    while offset < 0:
        triangle = next(triangles)
        vertices = triangle.exterior.coords[:3]
        points.extend(points_on_triangle(vertices, 1))
        offset += 1

    return points


def distribute_points(points, groups, fid):
    "Allocate randomized points to population groups"
    if len(groups) > 1:
        # don't bother shuffling if there's only one key
        random.shuffle(points)

    points = iter(points)
    for key, population in groups.items():
        chunk = itertools.islice(points, population)
        yield from (Point(x, y, key, fid) for x, y in chunk)


# https://stackoverflow.com/questions/47410054/generate-random-locations-within-a-triangular-domain
def points_on_triangle(vertices, n):
    """
    Give n random points uniformly on a triangle.

    The vertices of the triangle are given by the shape
    (2, 3) array *vertices*: one vertex per row.
    """
    x = np.sort(np.random.rand(2, n), axis=0)
    return np.column_stack([x[0], x[1] - x[0], 1.0 - x[1]]) @ vertices
