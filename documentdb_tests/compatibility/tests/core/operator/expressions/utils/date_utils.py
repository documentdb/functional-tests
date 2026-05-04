from calendar import timegm
from datetime import datetime, timezone

from bson import ObjectId, Timestamp


def ts_from_args(*args, inc=1) -> Timestamp:
    """Create a MongoDB Timestamp from a UTC datetime. e.g. ts_from_args(2024, 6, 15, 0, 0, 0)"""
    dt = datetime(*args, tzinfo=timezone.utc)  # type: ignore[misc]
    return Timestamp(timegm(dt.timetuple()), inc)


def oid_from_args(*args) -> ObjectId:
    """Create an ObjectId embedding a UTC datetime. e.g. oid_from_args(2024, 6, 15, 0, 0, 0)"""
    ts = timegm(datetime(*args, tzinfo=timezone.utc).timetuple())  # type: ignore[misc]
    return ObjectId(format(ts, "08x") + "0000000000000000")
