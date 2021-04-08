"""
This module defines an API for writing point data to different output formats.

Supported types include:

 - CSV
 - GeoJSON (newline-delimited)
 - Shapefile
 - SQLite
"""
import csv
import geojson
from pathlib import Path

from .point import Point


class Writer:
    """
    Base class for somewhat file-like output formatters

    path is a string or Path-like object, to a file
    mode is a writing mode, like in open() https://docs.python.org/3/library/functions.html#open
    **kwargs may be passed to underlying resources, like csv.writer
    """

    def __init__(self, path, mode="w", **kwargs):
        self.path = Path(path)
        self.mode = mode
        self._kwargs = kwargs

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close(type, value, traceback)

    def open(self):
        raise NotImplementedError

    def close(self, type, value, traceback):
        raise NotImplementedError

    def write(self, point):
        raise NotImplementedError

    def write_all(self, points):
        for point in points:
            self.write(point)


class CSVWriter(Writer):
    "Write points to a CSV file"

    def open(self):
        self.fd = open(self.path, self.mode)
        self.writer = csv.writer(self.fd, **self._kwargs)

        # new file, write headings
        if self.mode == "w":
            self.writer.writerow(Point._fields)

    def close(self, type, value, traceback):
        self.fd.close()

    def write(self, point):
        self.writer.writerow(point)

    def write_all(self, points):
        self.writer.writerows(points)


class GeoJSONWriter(Writer):
    "Write newline-delimited GeoJSON Point features to a file"

    def open(self):
        self.fd = open(self.path, self.mode)

    def write(self, point):
        geometry = geojson.Point([point.x, point.y])
        properties = {"group": point.group, "fid": point.fid}
        feature = geojson.Feature(geometry=geometry, properties=properties)
        data = geojson.dumps(feature) + "\n"
        self.fd.write(data)

    def close(self, type, value, traceback):
        self.fd.close()


FORMATS = {"csv": CSVWriter, "geojson": GeoJSONWriter}
FILE_TYPES = {".csv": CSVWriter, ".json": GeoJSONWriter, ".geojson": GeoJSONWriter}
