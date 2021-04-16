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

from .point import Point, Error
from .output import FILE_TYPES, FORMATS


def plot(src, dest, keys, format=None, mode="w", fid_field=None, coerce=False):
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
        for points, err in generate_points(
            src, *keys, fid_field=fid_field, coerce=coerce
        ):
            writer.write_all(points)
            if err.offset != 0:
                writer.write_error(err)


def generate_points(src, *keys, fid_field=None, coerce=False):
    """
    Generate dot-density data, reading from source and yielding points.
    Any keys given will be used to extract population properties from features.

    For each feature, yield a two-tuple of:
     - a list of Point objects
     - the error offset for this polygon-population combination
    """
    with fiona.open(src) as source:
        for feature in source:
            for key in keys:
                yield points_in_feature(
                    feature, key, fid_field=fid_field, coerce=coerce
                )


def points_in_feature(feature, key, fid_field=None, coerce=False):
    """
    Take a geojson *feature*, create a shape
    Get population from feature.properties using *key*
    Concatenate all points yielded from points_in_shape
    return a two-tuple of:
     - a list of Point objects
     - the error tuple, containing an offset, group name and feature id
    """
    if fid_field is not None:
        fid = feature["properties"].get(fid_field)
    else:
        fid = feature.get("id")

    geom = shape(feature["geometry"])
    population = feature["properties"].get(key) or 0  # handle missing or None
    if coerce:
        # let this fail if it fails
        population = int(population)

    points, err = points_in_shape(geom, population)
    points = [Point(x, y, key, fid) for (x, y) in points]
    return points, Error(err, key, fid)


def points_in_shape(geom, population):
    """
    plot n points randomly within a shapely geom
    first, cut the shape into triangles
    then, give each triangle a portion of points based on relative area
    within each triangle, distribute points using a weighted average
    return a two-tuple of:
     - a list of (x, y) coordinates
     - the error offset for this polygon-population combination
    """
    triangles = (t for t in triangulate(geom) if t.within(geom))
    points = []
    offset = -1 * population  # count up as we go
    for triangle in triangles:
        ratio = triangle.area / geom.area
        n = round(ratio * population)
        offset += n
        vertices = triangle.exterior.coords[:3]
        if n > 0:
            points.extend(points_on_triangle(vertices, n))

    return points, offset


# https://stackoverflow.com/questions/47410054/generate-random-locations-within-a-triangular-domain
def points_on_triangle(vertices, n):
    """
    Give n random points uniformly on a triangle.

    The vertices of the triangle are given by the shape
    (2, 3) array *vertices*: one vertex per row.
    """
    x = np.sort(np.random.rand(2, n), axis=0)
    return np.column_stack([x[0], x[1] - x[0], 1.0 - x[1]]) @ vertices
