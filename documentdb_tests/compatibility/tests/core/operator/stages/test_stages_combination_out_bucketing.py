"""$out stage — composition with bucketing and window stages.

The sibling ``test_stages_combination_out`` exercises $out after $match,
$project, $group, $sort/$limit, $unwind, $lookup and friends. This file
extends that composition coverage to the bucketing and window family that the
existing file does not touch: $bucket, $sortByCount, $setWindowFields, and
$bucketAuto.

$bucketAuto before $out writes the auto-bucketed output on native MongoDB,
exercised by ``test_out_after_bucketauto``.

Oracle: MongoDB 8.2.4 (functional-tests CI baseline).
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.out.utils.out_test_helpers import (
    OutTestCase,
    target_name,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.aggregate

# Property [Bucketing / Window Composition]: $out writes the output produced by
# a preceding bucketing or window stage unchanged.
OUT_WINDOW_BUCKET_TESTS: list[OutTestCase] = [
    OutTestCase(
        "bucket_then_out",
        docs=[{"_id": i, "x": v} for i, v in enumerate([1, 5, 12, 18, 22, 35], start=1)],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10, 20, 40],
                    "default": "other",
                    "output": {"count": {"$sum": 1}},
                }
            }
        ],
        expected=[
            {"_id": 0, "count": 2},
            {"_id": 10, "count": 2},
            {"_id": 20, "count": 2},
        ],
        msg="$out writes the per-bucket counts produced by a preceding $bucket.",
    ),
    OutTestCase(
        "sortbycount_then_out",
        docs=[
            {"_id": 1, "c": "a"},
            {"_id": 2, "c": "b"},
            {"_id": 3, "c": "a"},
            {"_id": 4, "c": "a"},
        ],
        pipeline=[{"$sortByCount": "$c"}],
        expected=[
            {"_id": "a", "count": 3},
            {"_id": "b", "count": 1},
        ],
        msg="$out writes the grouped counts produced by a preceding $sortByCount.",
    ),
    OutTestCase(
        "setwindowfields_then_out",
        docs=[
            {"_id": 1, "g": "a", "v": 10},
            {"_id": 2, "g": "a", "v": 20},
            {"_id": 3, "g": "b", "v": 30},
        ],
        pipeline=[
            {
                "$setWindowFields": {
                    "partitionBy": "$g",
                    "sortBy": {"_id": 1},
                    "output": {
                        "running": {
                            "$sum": "$v",
                            "window": {"documents": ["unbounded", "current"]},
                        }
                    },
                }
            }
        ],
        expected=[
            {"_id": 1, "g": "a", "v": 10, "running": 10},
            {"_id": 2, "g": "a", "v": 20, "running": 30},
            {"_id": 3, "g": "b", "v": 30, "running": 30},
        ],
        msg="$out writes the per-partition running totals from $setWindowFields.",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(OUT_WINDOW_BUCKET_TESTS))
def test_out_window_bucket_composition(collection, test_case: OutTestCase):
    """$out writes the output of a preceding bucketing or window stage."""
    populate_collection(collection, test_case)
    target = target_name(collection, test_case)
    pipeline = list(test_case.pipeline) + [test_case.build_out_stage(collection)]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    result = execute_command(
        collection,
        {"find": target, "filter": {}, "sort": {"_id": 1}},
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)
    collection.database.drop_collection(target)


def test_out_after_bucketauto(collection):
    """$out writes the auto-bucketed output produced by a preceding $bucketAuto."""
    collection.insert_many(
        [{"_id": i, "x": v} for i, v in enumerate([1, 5, 12, 18, 22, 35], start=1)]
    )
    target = f"{collection.name}_bucketauto_out"
    collection.database.drop_collection(target)
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$bucketAuto": {"groupBy": "$x", "buckets": 2}},
                {"$out": target},
            ],
            "cursor": {},
        },
    )
    written = execute_command(
        collection,
        {"find": target, "filter": {}, "sort": {"_id": 1}},
    )
    assertResult(
        written,
        expected=[
            {"_id": {"min": 1, "max": 18}, "count": 3},
            {"_id": {"min": 18, "max": 35}, "count": 3},
        ],
        msg="$out should persist the two auto-computed buckets from $bucketAuto.",
    )
    collection.database.drop_collection(target)
