"""Tests for $merge whenNotMatched type validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.merge.utils.merge_common import (
    TARGET,
    MergeTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

# Property [whenNotMatched Type Strictness]: only string, null, and undefined
# are accepted for the whenNotMatched field; all other BSON types produce
# TYPE_MISMATCH_ERROR.
MERGE_WHEN_NOT_MATCHED_TYPE_STRICTNESS_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        f"when_not_matched_type_{tid}",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": val}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$merge should reject {tid} for the whenNotMatched field",
    )
    for tid, val in [
        ("int32", 123),
        ("int64", Int64(123)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", ["insert"]),
        ("object", {"x": 1}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02")),
        ("regex", Regex("abc")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [whenNotMatched Invalid String Values]: invalid string values for
# whenNotMatched produce BAD_VALUE_ERROR; matching is case-sensitive.
MERGE_WHEN_NOT_MATCHED_INVALID_STRING_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        f"when_not_matched_str_{tid}",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": val}}],
        error_code=BAD_VALUE_ERROR,
        msg=f"$merge should reject '{val}' for whenNotMatched",
    )
    for tid, val in [
        ("empty", ""),
        ("invalid", "invalid"),
        ("case_insert", "Insert"),
        ("case_discard", "Discard"),
        ("case_fail", "FAIL"),
    ]
]

MERGE_WHEN_NOT_MATCHED_TYPE_ALL_TESTS = (
    MERGE_WHEN_NOT_MATCHED_TYPE_STRICTNESS_TESTS + MERGE_WHEN_NOT_MATCHED_INVALID_STRING_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_WHEN_NOT_MATCHED_TYPE_ALL_TESTS))
def test_stages_merge_when_not_matched_type(collection, test_case: MergeTestCase):
    """Test $merge whenNotMatched type strictness and invalid string values."""
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
