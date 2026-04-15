from calendar import timegm
from datetime import datetime

from bson import ObjectId, Timestamp


def ts_from_args(*args, inc=1) -> Timestamp:
    """Create a MongoDB Timestamp from a UTC datetime. e.g. ts_from_args(2024, 6, 15, 0, 0, 0)"""
    return Timestamp(timegm(datetime(*args).timetuple()), inc)


def oid_from_args(*args) -> ObjectId:
    """Create an ObjectId embedding a UTC datetime. e.g. oid_from_args(2024, 6, 15, 0, 0, 0)"""
    ts = timegm(datetime(*args).timetuple())
    return ObjectId(format(ts, "08x") + "0000000000000000")
