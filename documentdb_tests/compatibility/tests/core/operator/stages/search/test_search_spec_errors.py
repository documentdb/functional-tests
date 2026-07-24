"""Tests for $search stage spec and operator structural errors."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.search.utils.search_common import (
    SEARCH_INDEX_NAME,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

pytestmark = pytest.mark.requires(search=True)


# Property [Null Sub-field As Missing]: a null operator value or null required
# text sub-field (path/query) is treated as missing and hits the same
# downstream required-field error as omitting it entirely.
SEARCH_NULL_MISSING_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null_missing_operator",
        pipeline=[{"$search": {"text": None}}],
        error_code=UNKNOWN_ERROR,
        msg="$search should treat a null operator value as a missing operator and reject it",
    ),
    StageTestCase(
        "null_missing_text_query",
        pipeline=[
            {"$search": {"text": {"query": None, "path": "title"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should treat a null text.query as missing and reject the required query",
    ),
    StageTestCase(
        "null_missing_text_path",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": None}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should treat a null text.path as missing and reject the required path",
    ),
]

# Property [Operator Slot Missing]: a spec containing no recognized search
# operator (empty, options-only, or an unknown operator key) is rejected.
SEARCH_OPERATOR_MISSING_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "operator_missing_empty_spec",
        pipeline=[{"$search": {}}],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject an empty spec that contains no operator",
    ),
    StageTestCase(
        "operator_missing_options_only",
        pipeline=[{"$search": {"index": SEARCH_INDEX_NAME}}],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject an options-only spec that contains no operator",
    ),
    StageTestCase(
        "operator_missing_unknown_key",
        pipeline=[
            {"$search": {"bogus": {"query": "quick", "path": "title"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject an unknown operator key as no recognized operator",
    ),
]

# Property [Operator Slot Duplicate]: a spec containing more than one search
# operator is rejected.
SEARCH_OPERATOR_DUPLICATE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "operator_duplicate_two",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "exists": {"path": "title"},
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a spec containing two search operators",
    ),
]

# Property [Operator Value Type]: a recognized operator whose value is not a
# document is rejected (a null value is owned by the null-as-missing property
# above).
SEARCH_OPERATOR_VALUE_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"operator_value_{tid}",
        pipeline=[{"$search": {"text": val}}],
        error_code=UNKNOWN_ERROR,
        msg=f"$search should reject a {tid} operator value as a non-document",
    )
    for tid, val in [
        ("string", "quick"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("bool", True),
        ("array", ["quick"]),
        ("objectid", ObjectId("0123456789abcdef01234567")),
        ("datetime", datetime.datetime(2020, 1, 1)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
    ]
]

# Property [Operator Name Exact Match]: operator names are matched exactly
# (case-sensitive and not whitespace-trimmed).
SEARCH_OPERATOR_NAME_CASE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"operator_name_{tid}",
        pipeline=[
            {"$search": {name: {"query": "quick", "path": "title"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$search should reject the {tid} operator name as an unrecognized operator",
    )
    for tid, name in [
        ("capitalized", "Text"),
        ("trailing_space", "text "),
        ("leading_space", " text"),
    ]
]

SEARCH_SPEC_ERROR_TESTS = (
    SEARCH_NULL_MISSING_ERROR_TESTS
    + SEARCH_OPERATOR_MISSING_ERROR_TESTS
    + SEARCH_OPERATOR_DUPLICATE_ERROR_TESTS
    + SEARCH_OPERATOR_VALUE_TYPE_ERROR_TESTS
    + SEARCH_OPERATOR_NAME_CASE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_SPEC_ERROR_TESTS))
def test_search_spec_errors(indexed_collection, test_case: StageTestCase):
    """Test $search rejects null-as-missing sub-fields and operator structural errors."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
