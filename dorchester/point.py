# this is here to avoid a circular import
from collections import namedtuple


class Point(namedtuple("Point", ["x", "y", "group", "fid"])):
    @property
    def __geo_interface__(self):
        return {"type": "Point", "coordinates": (self.x, self.y)}

    def as_feature(self):
        geometry = self.__geo_interface__
        properties = {"group": self.group, "fid": self.fid}
        return {"type": "Feature", "properties": properties, "geometry": geometry}


# for structuring error offsets
Error = namedtuple("Error", ["offset", "group", "fid"])
