"""
The functions in this module outline the main API for creating the data behind dot density maps.
"""
import math
import sys
from itertools import chain
from pathlib import Path

import fiona
from fiona.crs import from_epsg

import geojson
import numpy as np
from shapely.geometry import shape
from shapely.ops import triangulate

from .point import Point
from .output import FILE_TYPES, FORMATS


def plot(src, dest, keys, format=None, mode="w"):
    """
    Read from source, write to dest.
    """
    src = Path(src)
    dest = Path(dest)

    if format in FORMATS:
        Writer = FORMATS[format]

    else:
        Writer = FILE_TYPES.get(dest.suffix, None)

    if Writer is None:
        raise TypeError(f"Unknown file type: {dest.name}")

    with Writer(dest, mode) as writer:
        writer.write_all(generate_points(src, *keys))


def generate_points(src, *keys):
    """
    Generate dot-density data, reading from source and yielding points.
    Any keys given will be used to extract population properties from features.
    """
    with fiona.open(src) as source:
        for feature in source:
            for key in keys:
                yield from points_in_feature(feature, key)


def points_in_feature(feature, key):
    """
    Take a geojson *feature*, create a shape
    Get population from feature.properties using *key*
    Concatenate all points yielded from points_in_shape
    """
    fid = feature.get("id")
    geom = shape(feature["geometry"])
    population = feature["properties"][key]
    for x, y in chain(*points_in_shape(geom, population)):
        yield Point(x, y, key, fid)


def points_in_shape(geom, population):
    """
    plot n points randomly within a shapely geom
    first, cut the shape into triangles
    then, give each triangle a portion of points based on relative area
    within each triangle, distribute points using a weighted average
    yield each set of points (one yield per triangle)
    """
    triangles = (t for t in triangulate(geom) if t.within(geom))
    for triangle in triangles:
        ratio = triangle.area / geom.area
        n = round(ratio * population)
        vertices = triangle.exterior.coords[:3]
        if n > 0:
            yield points_on_triangle(vertices, n)


# https://stackoverflow.com/questions/47410054/generate-random-locations-within-a-triangular-domain
def points_on_triangle(vertices, n):
    """
    Give n random points uniformly on a triangle.

    The vertices of the triangle are given by the shape
    (2, 3) array *vertices*: one vertex per row.
    """
    x = np.sort(np.random.rand(2, n), axis=0)
    return np.column_stack([x[0], x[1] - x[0], 1.0 - x[1]]) @ vertices
