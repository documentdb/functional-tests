"""$merge stage — pipeline integration with other stages (composition coverage).

Existing $merge coverage focuses on whenMatched/whenNotMatched semantics, the
``on`` field, and write-path behavior. This file mirrors the sibling
``test_stages_combination_out`` / ``test_stages_combination_sort`` pattern for
$merge: it verifies that $merge correctly consumes the output of a preceding
stage — $match filters, $project reshapes, $group aggregates into the ``_id``
key, $sort + $limit selects a top-k subset, $addFields enriches before a
default whenMatched merge into an existing target, and $unwind + $group
re-keys before writing.

Oracle: MongoDB 8.2.4 (functional-tests CI baseline). The engine under test
matches native behavior on every case; no engine divergences are tracked for
this surface.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.merge.utils.merge_common import (
    TARGET,
    MergeTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.aggregate

SOURCE = [
    {"_id": 1, "g": "a", "val": 10, "status": "on"},
    {"_id": 2, "g": "b", "val": 20, "status": "off"},
    {"_id": 3, "g": "a", "val": 30, "status": "on"},
]

# Property [Pipeline Integration]: $merge writes the output of the preceding
# stage to the target collection, preserving the transformation that stage
# produced.
MERGE_COMBINATION_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "match_then_merge",
        docs=SOURCE,
        target_docs=[],
        pipeline=[{"$match": {"status": "on"}}, {"$merge": {"into": TARGET}}],
        expected=[
            {"_id": 1, "g": "a", "val": 10, "status": "on"},
            {"_id": 3, "g": "a", "val": 30, "status": "on"},
        ],
        msg="$merge writes only the documents that pass a preceding $match.",
    ),
    MergeTestCase(
        "project_then_merge",
        docs=SOURCE,
        target_docs=[],
        pipeline=[{"$project": {"val": 1}}, {"$merge": {"into": TARGET}}],
        expected=[
            {"_id": 1, "val": 10},
            {"_id": 2, "val": 20},
            {"_id": 3, "val": 30},
        ],
        msg="$merge writes the reshaped documents produced by a preceding $project.",
    ),
    MergeTestCase(
        "group_then_merge",
        docs=SOURCE,
        target_docs=[],
        pipeline=[
            {"$group": {"_id": "$g", "total": {"$sum": "$val"}}},
            {"$merge": {"into": TARGET}},
        ],
        expected=[
            {"_id": "a", "total": 40},
            {"_id": "b", "total": 20},
        ],
        msg="$merge writes $group results keyed by the group _id.",
    ),
    MergeTestCase(
        "sort_limit_then_merge",
        docs=SOURCE,
        target_docs=[],
        pipeline=[
            {"$sort": {"val": -1}},
            {"$limit": 2},
            {"$merge": {"into": TARGET}},
        ],
        expected=[
            {"_id": 2, "g": "b", "val": 20, "status": "off"},
            {"_id": 3, "g": "a", "val": 30, "status": "on"},
        ],
        msg="$merge writes the top-k subset selected by a preceding $sort + $limit.",
    ),
    MergeTestCase(
        "addfields_then_merge_into_existing",
        docs=SOURCE,
        target_docs=[{"_id": 1, "note": "kept"}],
        pipeline=[
            {"$addFields": {"doubled": {"$multiply": ["$val", 2]}}},
            {"$merge": {"into": TARGET}},
        ],
        expected=[
            {"_id": 1, "note": "kept", "g": "a", "val": 10, "status": "on", "doubled": 20},
            {"_id": 2, "g": "b", "val": 20, "status": "off", "doubled": 40},
            {"_id": 3, "g": "a", "val": 30, "status": "on", "doubled": 60},
        ],
        msg="Default whenMatched merge keeps target fields and adds $addFields output.",
    ),
    MergeTestCase(
        "unwind_group_then_merge",
        docs=[{"_id": 1, "tags": ["x", "y"]}, {"_id": 2, "tags": ["x"]}],
        target_docs=[],
        pipeline=[
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "n": {"$sum": 1}}},
            {"$merge": {"into": TARGET}},
        ],
        expected=[
            {"_id": "x", "n": 2},
            {"_id": "y", "n": 1},
        ],
        msg="$merge writes counts produced by $unwind + $group re-keyed by tag.",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MERGE_COMBINATION_TESTS))
def test_stages_combination_merge(collection, test_case: MergeTestCase):
    """$merge writes the output of a preceding aggregation stage to the target."""
    target = test_case.prepare(collection)
    execute_command(collection, test_case.build_command(collection, target))
    result = execute_command(collection, {"find": target, "filter": {}, "sort": {"_id": 1}})
    assertResult(result, expected=test_case.expected, msg=test_case.msg)
