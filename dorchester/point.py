# this is here to avoid a circular import
from collections import namedtuple


class Point(namedtuple("Point", ["x", "y", "group", "fid"])):
    @property
    def __geo_interface__(self):
        return {"type": "Point", "coordinates": (self.x, self.y)}
