"""Tests for $merge let type strictness."""

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

# Property [let Type Strictness]: only object (document) and null are accepted
# for the let field; all other BSON types produce TYPE_MISMATCH_ERROR.
MERGE_LET_TYPE_STRICTNESS_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        f"let_type_{tid}",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "let": val, "whenMatched": [{"$set": {"x": 1}}]}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$merge should reject {tid} for the let field",
    )
    for tid, val in [
        ("int32", 123),
        ("int64", Int64(123)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "hello"),
        ("array", ["a", "b"]),
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


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_LET_TYPE_STRICTNESS_TESTS))
def test_stages_merge_let_type(collection, test_case: MergeTestCase):
    """Test $merge let type strictness."""
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
