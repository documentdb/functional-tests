"""Tests for $merge into type strictness."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.merge.utils.merge_common import (
    MergeTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    MERGE_INTO_TYPE_ERROR,
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

# Property [into Type Strictness - Document Form]: only string and document
# (object) are accepted for the into field; all other BSON types produce
# MERGE_INTO_TYPE_ERROR in the document form. String and object are the two
# valid forms, so they are not rejection cases here.
MERGE_INTO_TYPE_DOCUMENT_FORM_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        f"into_type_{tid}",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": val}}],
        error_code=MERGE_INTO_TYPE_ERROR,
        msg=f"$merge should reject {tid} for the into field",
    )
    for tid, val in [
        ("null", None),
        ("int32", 123),
        ("int64", Int64(123)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", ["target"]),
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

# Property [into Type Strictness - Simplified Form]: in the simplified form,
# type rejections produce TYPE_MISMATCH_ERROR instead of
# MERGE_INTO_TYPE_ERROR. String is the valid simplified form; object is the
# document form.
MERGE_INTO_TYPE_SIMPLIFIED_FORM_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        f"into_type_simplified_{tid}",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": val}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$merge simplified form should reject {tid}",
    )
    for tid, val in [
        ("null", None),
        ("int32", 123),
        ("int64", Int64(123)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", ["target"]),
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

MERGE_INTO_TYPE_STRICTNESS_TESTS = (
    MERGE_INTO_TYPE_DOCUMENT_FORM_TESTS + MERGE_INTO_TYPE_SIMPLIFIED_FORM_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_INTO_TYPE_STRICTNESS_TESTS))
def test_stages_merge_into_type(collection, test_case: MergeTestCase):
    """Test $merge into type strictness across simplified and document forms."""
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
