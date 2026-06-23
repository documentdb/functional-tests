"""Tests for the $search range operator."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.search.utils.search_common import (
    create_search_index,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework import fixtures
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    SEARCH_EXECUTOR_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_MAX,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MIN,
)

pytestmark = pytest.mark.requires(search=True)


_RANGE_DOCS = [
    {"_id": 1, "num": -5},
    {"_id": 2, "num": 0},
    {"_id": 3, "num": 5},
    {"_id": 4, "num": 10},
    {"_id": 5, "num": 20},
    {"_id": 6, "dt": datetime.datetime(1960, 1, 1)},  # pre-epoch
    {"_id": 7, "dt": datetime.datetime(1970, 1, 1)},  # epoch
    {"_id": 8, "dt": datetime.datetime(2020, 1, 1, 0, 0, 0, 123000)},  # sub-second
    {"_id": 9, "dt": datetime.datetime(9999, 12, 31)},  # far future
    {"_id": 10, "tok": "mango"},  # lowercase token
    {"_id": 11, "tok": "Mango"},  # capitalized token, sorts before lowercase
    {"_id": 12, "tok": ""},  # empty-string token, sorts first
    {"_id": 13, "tok": "papaya"},  # token sorting after mango
    {"_id": 14, "oid": ObjectId("000000000000000000000001")},
    {"_id": 15, "oid": ObjectId("000000000000000000000002")},
    {"_id": 16, "oid": ObjectId("000000000000000000000003")},
]

_RANGE_INDEX_DEFINITION = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "num": {"type": "number"},
            "dt": {"type": "date"},
            "tok": {"type": "token"},
            "oid": {"type": "objectId"},
        },
    }
}


@pytest.fixture(scope="module")
def range_collection(engine_client, worker_id):
    """A module-scoped collection with a static search index mapping a numeric, a
    date, and a token-typed field, shared read-only across the range cases so the
    index is built and polled once."""
    db_name = fixtures.generate_database_name("stages_search_range", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["range_op"]
    coll.insert_many(_RANGE_DOCS)
    create_search_index(coll, _RANGE_INDEX_DEFINITION)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


# Property [Range Numeric Bound Type And Value Acceptance]: range accepts int32,
# int64, and double numeric bounds (matching identically for the same value)
# across the full numeric range with no error.
SEARCH_RANGE_NUMERIC_BOUND_TESTS: list[StageTestCase] = [
    StageTestCase(
        "numeric_bound_int32",
        pipeline=[{"$search": {"range": {"path": "num", "lte": 5}}}],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
            ]
        },
        msg="$search range should apply an int32 numeric bound",
    ),
    StageTestCase(
        "numeric_bound_int64",
        pipeline=[
            {"$search": {"range": {"path": "num", "lte": Int64(5)}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
            ]
        },
        msg="$search range should apply an int64 numeric bound identically to int32",
    ),
    StageTestCase(
        "numeric_bound_double",
        pipeline=[{"$search": {"range": {"path": "num", "lte": 5.0}}}],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
            ]
        },
        msg="$search range should apply a double numeric bound identically to int32",
    ),
    StageTestCase(
        "numeric_bound_negative",
        pipeline=[{"$search": {"range": {"path": "num", "lte": -5}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search range should apply a negative numeric bound",
    ),
    StageTestCase(
        "numeric_bound_zero",
        pipeline=[{"$search": {"range": {"path": "num", "lt": 0}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search range should apply a zero numeric bound",
    ),
    StageTestCase(
        "numeric_bound_negative_zero",
        pipeline=[
            {"$search": {"range": {"path": "num", "lt": DOUBLE_NEGATIVE_ZERO}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search range should treat a -0.0 bound identically to a 0 bound",
    ),
    StageTestCase(
        "numeric_bound_subnormal",
        # The smallest positive subnormal double is a tiny positive bound, so it
        # excludes the 0 and -5 docs that a 0 bound would otherwise admit.
        pipeline=[
            {"$search": {"range": {"path": "num", "gte": DOUBLE_MIN_SUBNORMAL}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 3),
                Contains("_id", 4),
                Contains("_id", 5),
            ]
        },
        msg="$search range should apply the smallest subnormal double as a tiny positive bound",
    ),
    StageTestCase(
        "numeric_bound_int32_min",
        pipeline=[
            {"$search": {"range": {"path": "num", "gte": INT32_MIN}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(5),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
                Contains("_id", 5),
            ]
        },
        msg="$search range should apply an int32-min bound, admitting every greater document",
    ),
    StageTestCase(
        "numeric_bound_double_max",
        pipeline=[
            {"$search": {"range": {"path": "num", "gt": DOUBLE_MAX}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search range should apply a DBL_MAX bound, matching nothing in a finite sample",
    ),
]

# Property [Range Datetime Bound Full Precision]: a datetime bound on a date path
# honors full millisecond precision.
SEARCH_RANGE_DATE_BOUND_TESTS: list[StageTestCase] = [
    StageTestCase(
        "date_bound_epoch",
        pipeline=[
            {"$search": {"range": {"path": "dt", "gte": datetime.datetime(1970, 1, 1)}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 7),
                Contains("_id", 8),
                Contains("_id", 9),
            ]
        },
        msg="$search range should apply an epoch bound, excluding the pre-epoch document",
    ),
    StageTestCase(
        "date_bound_pre_epoch",
        pipeline=[
            {"$search": {"range": {"path": "dt", "lt": datetime.datetime(1970, 1, 1)}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 6)]},
        msg="$search range should select the pre-epoch document below an epoch bound",
    ),
    StageTestCase(
        "date_bound_far_future",
        pipeline=[
            {"$search": {"range": {"path": "dt", "gte": datetime.datetime(9999, 12, 31)}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 9)]},
        msg="$search range should apply a far-future year-9999 bound",
    ),
    StageTestCase(
        "date_bound_millisecond_exact",
        pipeline=[
            {
                "$search": {
                    "range": {
                        "path": "dt",
                        "gte": datetime.datetime(2020, 1, 1, 0, 0, 0, 123000),
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 8), Contains("_id", 9)]},
        msg="$search range should select the millisecond-precision document at its exact bound",
    ),
    StageTestCase(
        "date_bound_millisecond_after",
        # One millisecond past the stored sub-second time excludes that document,
        # so the bound's millisecond component is honored rather than truncated.
        pipeline=[
            {
                "$search": {
                    "range": {
                        "path": "dt",
                        "gte": datetime.datetime(2020, 1, 1, 0, 0, 0, 124000),
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 9)]},
        msg="$search range should honor the millisecond component of a datetime bound",
    ),
]

# Property [Range Inclusive And Exclusive Bounds]: gte and lte include the
# boundary value while gt and lt exclude it, and an inclusive degenerate interval
# (gte equal to lte) matches the boundary value.
SEARCH_RANGE_INCLUSIVE_EXCLUSIVE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "inclusive_gte",
        pipeline=[{"$search": {"range": {"path": "num", "gte": 10}}}],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 4), Contains("_id", 5)]},
        msg="$search range gte should include the boundary value",
    ),
    StageTestCase(
        "exclusive_gt",
        pipeline=[{"$search": {"range": {"path": "num", "gt": 10}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 5)]},
        msg="$search range gt should exclude the boundary value",
    ),
    StageTestCase(
        "inclusive_lte",
        pipeline=[{"$search": {"range": {"path": "num", "lte": 10}}}],
        expected={
            "cursor.firstBatch": [
                Len(4),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search range lte should include the boundary value",
    ),
    StageTestCase(
        "exclusive_lt",
        pipeline=[{"$search": {"range": {"path": "num", "lt": 10}}}],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
            ]
        },
        msg="$search range lt should exclude the boundary value",
    ),
    StageTestCase(
        "degenerate_inclusive_interval",
        pipeline=[
            {"$search": {"range": {"path": "num", "gte": 10, "lte": 10}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 4)]},
        msg="$search range should match the boundary value for an inclusive degenerate interval",
    ),
]

# Property [Range Non-Finite Bounds]: a +inf bound matches no documents, a -inf
# bound matches every document, and a NaN bound matches no documents, all with no
# error.
SEARCH_RANGE_NON_FINITE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "non_finite_positive_infinity",
        pipeline=[
            {"$search": {"range": {"path": "num", "gte": FLOAT_INFINITY}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search range should match no documents for a +inf bound",
    ),
    StageTestCase(
        "non_finite_negative_infinity",
        pipeline=[
            {"$search": {"range": {"path": "num", "gte": FLOAT_NEGATIVE_INFINITY}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(5),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
                Contains("_id", 5),
            ]
        },
        msg="$search range should match every document for a -inf bound",
    ),
    StageTestCase(
        "non_finite_nan",
        pipeline=[
            {"$search": {"range": {"path": "num", "gte": FLOAT_NAN}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search range should match no documents for a NaN bound",
    ),
]

# Property [Range Type-Mismatched Bound Silent No-Match]: a string bound on a
# numeric path and a numeric bound on a token/string path each return no documents
# with no error.
SEARCH_RANGE_TYPE_MISMATCH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "mismatch_string_bound_numeric_path",
        pipeline=[{"$search": {"range": {"path": "num", "gte": "5"}}}],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search range should return no documents and no error for a string bound on a "
        "numeric path",
    ),
    StageTestCase(
        "mismatch_numeric_bound_token_path",
        pipeline=[{"$search": {"range": {"path": "tok", "gte": 5}}}],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search range should return no documents and no error for a numeric bound on a "
        "token path",
    ),
]

# Property [Range Lexicographic Case-Sensitive Order]: over a token-mapped path,
# string range bounds compare in raw code-point order with no case folding.
SEARCH_RANGE_LEXICOGRAPHIC_ORDER_TESTS: list[StageTestCase] = [
    StageTestCase(
        "lexicographic_capital_in_upper_range",
        pipeline=[
            {"$search": {"range": {"path": "tok", "gte": "A", "lte": "z"}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 10),
                Contains("_id", 11),
                Contains("_id", 13),
            ]
        },
        msg="$search range should include a capitalized token within an A-to-z code-point range",
    ),
    StageTestCase(
        "lexicographic_capital_excluded_below_lowercase",
        pipeline=[
            {"$search": {"range": {"path": "tok", "gte": "m", "lte": "z"}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 10), Contains("_id", 13)]},
        msg="$search range should exclude a capitalized token below a lowercase lower bound, "
        "confirming case sensitivity",
    ),
]

# Property [Range String Inclusive And Exclusive Bounds]: gte and lte include a
# string bound while gt and lt exclude it, and an inclusive degenerate interval
# matches the boundary token.
SEARCH_RANGE_STRING_INCLUSIVE_EXCLUSIVE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "string_gte_lte_include_bounds",
        pipeline=[
            {"$search": {"range": {"path": "tok", "gte": "mango", "lte": "papaya"}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 10), Contains("_id", 13)]},
        msg="$search range gte and lte should include both string boundary tokens",
    ),
    StageTestCase(
        "string_gt_excludes_lower",
        pipeline=[
            {"$search": {"range": {"path": "tok", "gt": "mango", "lte": "papaya"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 13)]},
        msg="$search range gt should exclude the lower string boundary token",
    ),
    StageTestCase(
        "string_lt_excludes_upper",
        pipeline=[
            {"$search": {"range": {"path": "tok", "gte": "mango", "lt": "papaya"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 10)]},
        msg="$search range lt should exclude the upper string boundary token",
    ),
    StageTestCase(
        "string_degenerate_inclusive",
        pipeline=[
            {"$search": {"range": {"path": "tok", "gte": "mango", "lte": "mango"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 10)]},
        msg="$search range should match the boundary token for an inclusive degenerate string "
        "interval",
    ),
]

# Property [Range Empty-String Bounds]: an empty-string lower bound matches every
# stored token while an empty-string upper bound matches only the stored
# empty-string token.
SEARCH_RANGE_EMPTY_STRING_BOUND_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_string_gte_matches_all",
        pipeline=[{"$search": {"range": {"path": "tok", "gte": ""}}}],
        expected={
            "cursor.firstBatch": [
                Len(4),
                Contains("_id", 10),
                Contains("_id", 11),
                Contains("_id", 12),
                Contains("_id", 13),
            ]
        },
        msg="$search range should match every stored token for an empty-string lower bound",
    ),
    StageTestCase(
        "empty_string_lte_matches_empty_only",
        pipeline=[{"$search": {"range": {"path": "tok", "lte": ""}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 12)]},
        msg="$search range should match only the empty-string token for an empty-string upper "
        "bound",
    ),
]

# Property [Range ObjectId Bounds]: ObjectId is a supported bound type, so over an
# objectId-mapped path the bounds order by ObjectId value, with gte/lte inclusive
# and gt/lt exclusive.
SEARCH_RANGE_OBJECTID_BOUND_TESTS: list[StageTestCase] = [
    StageTestCase(
        "objectid_gte",
        pipeline=[
            {"$search": {"range": {"path": "oid", "gte": ObjectId("000000000000000000000002")}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 15), Contains("_id", 16)]},
        msg="$search range gte should include the boundary ObjectId and every greater one",
    ),
    StageTestCase(
        "objectid_gt",
        pipeline=[
            {"$search": {"range": {"path": "oid", "gt": ObjectId("000000000000000000000002")}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 16)]},
        msg="$search range gt should exclude the boundary ObjectId",
    ),
    StageTestCase(
        "objectid_lte",
        pipeline=[
            {"$search": {"range": {"path": "oid", "lte": ObjectId("000000000000000000000002")}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 14), Contains("_id", 15)]},
        msg="$search range lte should include the boundary ObjectId and every lesser one",
    ),
]

SEARCH_RANGE_TESTS = (
    SEARCH_RANGE_NUMERIC_BOUND_TESTS
    + SEARCH_RANGE_DATE_BOUND_TESTS
    + SEARCH_RANGE_INCLUSIVE_EXCLUSIVE_TESTS
    + SEARCH_RANGE_NON_FINITE_TESTS
    + SEARCH_RANGE_TYPE_MISMATCH_TESTS
    + SEARCH_RANGE_LEXICOGRAPHIC_ORDER_TESTS
    + SEARCH_RANGE_STRING_INCLUSIVE_EXCLUSIVE_TESTS
    + SEARCH_RANGE_EMPTY_STRING_BOUND_TESTS
    + SEARCH_RANGE_OBJECTID_BOUND_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_RANGE_TESTS))
def test_search_range_cases(range_collection, test_case: StageTestCase):
    """Test $search range numeric, datetime, and lexicographic string bound semantics."""
    result = execute_command(
        range_collection,
        {"aggregate": range_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [Range Bound Unsupported Type]: number, string, date, and ObjectId are
# the supported bound types, so a bound of any other type is rejected regardless
# of the path type.
SEARCH_RANGE_BOUND_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"bound_type_{tid}",
        pipeline=[
            {"$search": {"range": {"path": "num", "gte": val}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg=f"$search range should reject a {tid} bound as an unsupported type",
    )
    for tid, val in [
        ("bool", True),
        ("object", {"a": 1}),
        ("array", [1, 2]),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("null", None),
    ]
]

# Property [Range String Bound On Date Path]: a string bound on a date path is
# rejected as needing a token index, unlike a string bound on a numeric path
# which returns no documents with no error.
SEARCH_RANGE_STRING_BOUND_DATE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "string_bound_date_path",
        pipeline=[
            {"$search": {"range": {"path": "dt", "gte": "2020-01-01"}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search range should reject a string bound on a date path as needing a token index",
    ),
]

# Property [Range Requires A Bound]: a range specifying none of lt/lte/gt/gte is
# rejected.
SEARCH_RANGE_NO_BOUND_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "no_bound",
        pipeline=[{"$search": {"range": {"path": "num"}}}],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search range should reject a spec that specifies no bound",
    ),
]

# Property [Range Single Bound Per Direction]: specifying both bounds for one
# direction (gt and gte, or lt and lte) is rejected.
SEARCH_RANGE_DUPLICATE_BOUND_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "duplicate_lower_bound",
        pipeline=[
            {"$search": {"range": {"path": "num", "gt": 0, "gte": 0}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search range should reject specifying both gt and gte",
    ),
    StageTestCase(
        "duplicate_upper_bound",
        pipeline=[
            {"$search": {"range": {"path": "num", "lt": 10, "lte": 10}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search range should reject specifying both lt and lte",
    ),
]

# Property [Range Interval Validity]: an inverted interval (gte greater than lte)
# and an exclusive degenerate interval (gt equal to lt) are rejected.
SEARCH_RANGE_INTERVAL_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "inverted_interval",
        pipeline=[
            {"$search": {"range": {"path": "num", "gte": 10, "lte": 5}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search range should reject an inverted interval where gte exceeds lte",
    ),
    StageTestCase(
        "exclusive_degenerate_interval",
        pipeline=[
            {"$search": {"range": {"path": "num", "gt": 5, "lt": 5}}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search range should reject an exclusive degenerate interval where gt equals lt",
    ),
]

SEARCH_RANGE_ERROR_TESTS = (
    SEARCH_RANGE_BOUND_TYPE_ERROR_TESTS
    + SEARCH_RANGE_STRING_BOUND_DATE_ERROR_TESTS
    + SEARCH_RANGE_NO_BOUND_ERROR_TESTS
    + SEARCH_RANGE_DUPLICATE_BOUND_ERROR_TESTS
    + SEARCH_RANGE_INTERVAL_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_RANGE_ERROR_TESTS))
def test_search_range_errors(range_collection, test_case: StageTestCase):
    """Test $search range rejects unsupported bound types and invalid bound intervals."""
    result = execute_command(
        range_collection,
        {"aggregate": range_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
