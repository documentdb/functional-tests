"""Tests for $merge write-path field ordering and Timestamp replacement."""

from __future__ import annotations

import pytest
from bson import Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.merge.utils.merge_common import (
    TARGET,
    MergeTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)
from documentdb_tests.framework.property_checks import (
    Eq,
    IsType,
    Ne,
    OrderedKeys,
)

# Property [Field Order on Insert]: when whenMatched is "merge" or
# "keepExisting", the insert path reorders fields alphabetically with _id
# first; when whenMatched is "replace" or a pipeline, the insert path
# preserves source field order.
MERGE_FIELD_ORDER_ON_INSERT_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "field_order_insert_merge_alphabetical",
        docs=[{"_id": 1, "z": 1, "a": 2, "m": 3}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "merge"}}],
        expected=["_id", "a", "m", "z"],
        msg="$merge insert path should reorder fields alphabetically when whenMatched is merge",
    ),
    MergeTestCase(
        "field_order_insert_keep_existing_alphabetical",
        docs=[{"_id": 1, "z": 1, "a": 2, "m": 3}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "keepExisting"}}],
        expected=["_id", "a", "m", "z"],
        msg="$merge insert path should reorder fields alphabetically with keepExisting",
    ),
    MergeTestCase(
        "field_order_insert_replace_preserves_order",
        docs=[{"_id": 1, "z": 1, "a": 2, "m": 3}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "replace"}}],
        expected=["_id", "z", "a", "m"],
        msg="$merge insert path should preserve source field order when whenMatched is replace",
    ),
    MergeTestCase(
        "field_order_insert_pipeline_preserves_order",
        docs=[{"_id": 1, "z": 1, "a": 2, "m": 3}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": [{"$set": {"x": 1}}]}}],
        expected=["_id", "z", "a", "m"],
        msg="$merge insert path should preserve source field order when whenMatched is a pipeline",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_FIELD_ORDER_ON_INSERT_TESTS))
def test_stages_merge_field_order_on_insert(collection, test_case: MergeTestCase):
    """Test $merge field order on the insert path."""
    target = test_case.prepare(collection)
    execute_command(collection, test_case.build_command(collection, target))

    # Read the stored document back as-is; the find response preserves the
    # server's field order, which OrderedKeys asserts directly.
    result = execute_command(collection, {"find": target, "filter": {}})
    assertResult(
        result,
        expected={"cursor.firstBatch.0": OrderedKeys(test_case.expected)},
        raw_res=True,
        msg=test_case.msg,
    )


# Property [Timestamp(0,0) Insert Path Replaced]: Timestamp(0,0) in a
# non-_id field is replaced by the server with the current time on the
# insert path regardless of the whenMatched mode.
MERGE_TIMESTAMP_INSERT_REPLACED_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "ts_insert_replace_mode",
        docs=[{"_id": 1, "ts": Timestamp(0, 0), "val": "x"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "replace"}}],
        expected={"ts": [IsType("timestamp"), Ne(Timestamp(0, 0))]},
        msg="$merge should replace Timestamp(0,0) on insert path with whenMatched replace",
    ),
    MergeTestCase(
        "ts_insert_fail_mode",
        docs=[{"_id": 1, "ts": Timestamp(0, 0), "val": "x"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "fail"}}],
        expected={"ts": [IsType("timestamp"), Ne(Timestamp(0, 0))]},
        msg="$merge should replace Timestamp(0,0) on insert path with whenMatched fail",
    ),
    MergeTestCase(
        "ts_insert_pipeline_mode",
        docs=[{"_id": 1, "ts": Timestamp(0, 0), "val": "x"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": [{"$set": {"x": 1}}]}}],
        expected={"ts": [IsType("timestamp"), Ne(Timestamp(0, 0))]},
        msg="$merge should replace Timestamp(0,0) on insert path with whenMatched pipeline",
    ),
    MergeTestCase(
        "ts_insert_merge_mode",
        docs=[{"_id": 1, "ts": Timestamp(0, 0), "val": "x"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "merge"}}],
        expected={"ts": [IsType("timestamp"), Ne(Timestamp(0, 0))]},
        msg="$merge should replace Timestamp(0,0) on insert path with whenMatched merge",
    ),
    MergeTestCase(
        "ts_insert_keep_existing_mode",
        docs=[{"_id": 1, "ts": Timestamp(0, 0), "val": "x"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "keepExisting"}}],
        expected={"ts": [IsType("timestamp"), Ne(Timestamp(0, 0))]},
        msg="$merge should replace Timestamp(0,0) on insert path with whenMatched keepExisting",
    ),
]

# Property [Timestamp(0,0) Matched Path Replaced]: on the matched path,
# Timestamp(0,0) is replaced by the server with the current time.
MERGE_TIMESTAMP_MATCHED_REPLACED_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "ts_matched_replace_mode",
        target_docs=[{"_id": 1, "old": "target"}],
        docs=[{"_id": 1, "ts": Timestamp(0, 0), "val": "new"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "replace"}}],
        expected={"ts": [IsType("timestamp"), Ne(Timestamp(0, 0))]},
        msg="$merge should replace Timestamp(0,0) on matched path with replace mode",
    ),
    MergeTestCase(
        "ts_matched_merge_mode",
        target_docs=[{"_id": 1, "old": "target"}],
        docs=[{"_id": 1, "ts": Timestamp(0, 0), "val": "new"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "merge"}}],
        expected={"ts": [IsType("timestamp"), Ne(Timestamp(0, 0))]},
        msg="$merge should replace Timestamp(0,0) on matched path with merge mode",
    ),
    MergeTestCase(
        "ts_matched_pipeline_set",
        target_docs=[{"_id": 1, "old": "target"}],
        docs=[{"_id": 1, "ts": Timestamp(0, 0), "val": "new"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": [{"$set": {"ts": "$$new.ts"}}]}}],
        expected={"ts": [IsType("timestamp"), Ne(Timestamp(0, 0))]},
        msg="$merge should replace Timestamp(0,0) on matched path with pipeline $set",
    ),
]

# Property [Non-Zero Timestamp Preserved]: non-zero Timestamp values are
# always preserved regardless of mode on both insert and matched paths.
MERGE_TIMESTAMP_NONZERO_PRESERVED_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "ts_nonzero_insert_replace",
        docs=[{"_id": 1, "ts": Timestamp(100, 5), "val": "x"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "replace"}}],
        expected={"ts": [IsType("timestamp"), Eq(Timestamp(100, 5))]},
        msg="$merge should preserve non-zero Timestamp on insert path with replace mode",
    ),
    MergeTestCase(
        "ts_nonzero_insert_merge",
        docs=[{"_id": 1, "ts": Timestamp(100, 5), "val": "x"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "merge"}}],
        expected={"ts": [IsType("timestamp"), Eq(Timestamp(100, 5))]},
        msg="$merge should preserve non-zero Timestamp on insert path with merge mode",
    ),
    MergeTestCase(
        "ts_nonzero_matched_replace",
        target_docs=[{"_id": 1, "old": "target"}],
        docs=[{"_id": 1, "ts": Timestamp(100, 5), "val": "new"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "replace"}}],
        expected={"ts": [IsType("timestamp"), Eq(Timestamp(100, 5))]},
        msg="$merge should preserve non-zero Timestamp on matched path with replace mode",
    ),
    MergeTestCase(
        "ts_nonzero_matched_merge",
        target_docs=[{"_id": 1, "old": "target"}],
        docs=[{"_id": 1, "ts": Timestamp(100, 5), "val": "new"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "merge"}}],
        expected={"ts": [IsType("timestamp"), Eq(Timestamp(100, 5))]},
        msg="$merge should preserve non-zero Timestamp on matched path with merge mode",
    ),
]

# Property [Timestamp(0,0) in _id Field Preserved]: Timestamp(0,0) is NOT
# replaced when it appears as the _id field, unlike non-_id fields.
MERGE_TIMESTAMP_ID_FIELD_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "ts_id_insert_preserved",
        docs=[{"_id": Timestamp(0, 0), "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "replace"}}],
        expected={"_id": [IsType("timestamp"), Eq(Timestamp(0, 0))]},
        msg="$merge should NOT replace Timestamp(0,0) when it is the _id field on insert path",
    ),
    MergeTestCase(
        "ts_id_matched_preserved",
        target_docs=[{"_id": Timestamp(0, 0), "old": "target"}],
        docs=[{"_id": Timestamp(0, 0), "val": "new"}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "replace"}}],
        expected={"_id": [IsType("timestamp"), Eq(Timestamp(0, 0))]},
        msg="$merge should NOT replace Timestamp(0,0) when it is the _id field on matched path",
    ),
]

MERGE_TIMESTAMP_TESTS = (
    MERGE_TIMESTAMP_INSERT_REPLACED_TESTS
    + MERGE_TIMESTAMP_MATCHED_REPLACED_TESTS
    + MERGE_TIMESTAMP_NONZERO_PRESERVED_TESTS
    + MERGE_TIMESTAMP_ID_FIELD_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_TIMESTAMP_TESTS))
def test_stages_merge_timestamp_behavior(collection, test_case: MergeTestCase):
    """Test $merge Timestamp(0,0) replacement behavior.

    Each case reads back the stored ``ts`` and asserts its type plus whether it
    still equals the source value (preserved) or differs (replaced), via the
    property checks carried in ``expected``.
    """
    target = test_case.prepare(collection)
    result = execute_command(collection, test_case.build_command(collection, target))
    if test_case.error_code is None:
        result = execute_command(collection, {"find": target, "filter": {}, "sort": {"_id": 1}})
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
