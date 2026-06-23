"""Tests for $search cross-cutting stage option validation errors."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    SEARCH_EXECUTOR_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    INT32_MAX,
)

pytestmark = pytest.mark.requires(search=True)


# Property [Document-Typed Option Non-Document]: the count, highlight, and sort
# options must each be a document (a null value is treated as omitted).
SEARCH_DOCUMENT_OPTION_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"{opt}_type_{tid}",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, opt: val}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg=f"$search should reject a {tid} {opt} option as a non-document",
    )
    for opt in ("count", "highlight", "sort")
    for tid, val in [
        ("string", "x"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("bool", True),
        ("array", [{}]),
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

# Property [phrase.slop Bound And Shared Integer Coercion]: phrase.slop has a
# non-negative bound (it accepts zero, unlike the positive-bound highlight integer
# sub-fields) and exercises the shared $search integer parser, which rejects a
# fractional, non-finite, or out-of-32-bit-range numeric value.
SEARCH_INTEGER_COERCION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "slop_negative",
        pipeline=[
            {"$search": {"phrase": {"query": "quick brown", "path": "title", "slop": -1}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject a negative phrase.slop",
    ),
    StageTestCase(
        "slop_fractional_double",
        pipeline=[
            {"$search": {"phrase": {"query": "quick brown", "path": "title", "slop": 1.5}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject a fractional-double phrase.slop as a non-integer",
    ),
    StageTestCase(
        "slop_nan",
        pipeline=[
            {"$search": {"phrase": {"query": "quick brown", "path": "title", "slop": FLOAT_NAN}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject a NaN phrase.slop as a non-integer",
    ),
    StageTestCase(
        "slop_positive_infinity",
        pipeline=[
            {
                "$search": {
                    "phrase": {"query": "quick brown", "path": "title", "slop": FLOAT_INFINITY}
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject an infinite phrase.slop as not fitting in a 32-bit integer",
    ),
    StageTestCase(
        "slop_int64_over_int32",
        pipeline=[
            {
                "$search": {
                    "phrase": {
                        "query": "quick brown",
                        "path": "title",
                        "slop": Int64(INT32_MAX + 1),
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject an int64 phrase.slop past the 32-bit integer range",
    ),
]

# Property [Shared Integer Type Rejection]: the shared $search integer parser,
# exercised here through phrase.slop, accepts only whole numbers, so any
# non-numeric BSON type (plus Decimal128) is rejected.
SEARCH_INTEGER_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"slop_type_{tid}",
        pipeline=[
            {"$search": {"phrase": {"query": "quick brown", "path": "title", "slop": val}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg=f"$search should reject a {tid} phrase.slop as a non-integer",
    )
    for tid, val in [
        ("string", "1"),
        ("bool", True),
        ("object", {"a": 1}),
        ("array", [1]),
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

# Property [Unknown And Case-Variant Option]: an unknown top-level option field is
# rejected, and option names are matched exactly (case-sensitive and not
# whitespace-trimmed).
SEARCH_UNKNOWN_OPTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "option_unknown_field",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "bogus": 1}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject an unknown top-level option field",
    ),
    *[
        StageTestCase(
            f"option_name_{tid}",
            pipeline=[
                {"$search": {"text": {"query": "quick", "path": "title"}, name: value}},
            ],
            error_code=SEARCH_EXECUTOR_ERROR,
            msg=f"$search should reject the {tid} option name as an unrecognized option",
        )
        for tid, name, value in [
            ("capitalized_index", "Index", "default"),
            ("trailing_space_index", "index ", "default"),
        ]
    ],
]

SEARCH_OPTION_GENERAL_ERROR_TESTS = (
    SEARCH_DOCUMENT_OPTION_TYPE_ERROR_TESTS
    + SEARCH_INTEGER_COERCION_ERROR_TESTS
    + SEARCH_INTEGER_TYPE_ERROR_TESTS
    + SEARCH_UNKNOWN_OPTION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_OPTION_GENERAL_ERROR_TESTS))
def test_search_option_errors(indexed_collection, test_case: StageTestCase):
    """Test $search cross-cutting option validation: type, integer coercion, unknown options."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
