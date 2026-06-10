"""Tests for $merge whenMatched type validation."""

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
    MERGE_WHEN_MATCHED_TYPE_ERROR,
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

# Property [whenMatched Type Strictness]: only string and array are accepted
# for the whenMatched field; all other BSON types produce
# MERGE_WHEN_MATCHED_TYPE_ERROR.
MERGE_WHEN_MATCHED_TYPE_STRICTNESS_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        f"when_matched_type_{tid}",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": val}}],
        error_code=MERGE_WHEN_MATCHED_TYPE_ERROR,
        msg=f"$merge should reject {tid} for the whenMatched field",
    )
    for tid, val in [
        ("null", None),
        ("int32", 123),
        ("int64", Int64(123)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
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

# Property [whenMatched Invalid String Values]: invalid string values for
# whenMatched produce BAD_VALUE_ERROR; matching is case-sensitive.
MERGE_WHEN_MATCHED_INVALID_STRING_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        f"when_matched_str_{tid}",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": val}}],
        error_code=BAD_VALUE_ERROR,
        msg=f"$merge should reject '{val}' for whenMatched",
    )
    for tid, val in [
        ("empty", ""),
        ("invalid", "invalid"),
        ("case_merge", "Merge"),
        ("case_replace", "Replace"),
        ("case_keep_existing", "keepexisting"),
        ("case_fail", "FAIL"),
    ]
]

MERGE_WHEN_MATCHED_TYPE_ALL_TESTS = (
    MERGE_WHEN_MATCHED_TYPE_STRICTNESS_TESTS + MERGE_WHEN_MATCHED_INVALID_STRING_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_WHEN_MATCHED_TYPE_ALL_TESTS))
def test_stages_merge_when_matched_type(collection, test_case: MergeTestCase):
    """Test $merge whenMatched type strictness and invalid string values."""
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
