# this is here to avoid a circular import
from collections import namedtuple

Point = namedtuple("Point", ["x", "y", "group", "fid"])
