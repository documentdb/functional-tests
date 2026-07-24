"""Shared constants for $bucketAuto tests."""

from __future__ import annotations

# The preferred-number series accepted by the $bucketAuto 'granularity' option.
# See https://www.mongodb.com/docs/manual/reference/operator/aggregation/bucketAuto/
GRANULARITY_VALUES = [
    "R5",
    "R10",
    "R20",
    "R40",
    "R80",
    "1-2-5",
    "E6",
    "E12",
    "E24",
    "E48",
    "E96",
    "E192",
    "POWERSOF2",
]
