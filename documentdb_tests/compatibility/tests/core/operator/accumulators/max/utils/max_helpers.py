"""Pipeline helpers for $max accumulator tests."""

from __future__ import annotations

from typing import Any


def group_max(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $group pipeline that computes $max."""
    return [
        {"$group": {"_id": None, "result": {"$max": accumulator}}},
        {"$project": {"_id": 0, "result": 1}},
    ]


def bucket_max(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $bucket pipeline that computes $max."""
    return [
        {
            "$bucket": {
                "groupBy": {"$literal": 0},
                "boundaries": [-1, 1],
                "output": {"result": {"$max": accumulator}},
            }
        },
        {"$project": {"_id": 0, "result": 1}},
    ]


def bucket_auto_max(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $bucketAuto pipeline that computes $max."""
    return [
        {
            "$bucketAuto": {
                "groupBy": {"$literal": 0},
                "buckets": 1,
                "output": {"result": {"$max": accumulator}},
            }
        },
        {"$project": {"_id": 0, "result": 1}},
    ]


def group_max_with_type(accumulator: Any) -> list[dict[str, Any]]:
    """Build a $group pipeline that computes $max with $type projection."""
    return [
        {"$group": {"_id": None, "result": {"$max": accumulator}}},
        {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
    ]
