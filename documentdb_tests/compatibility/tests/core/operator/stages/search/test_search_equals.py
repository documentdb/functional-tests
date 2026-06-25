"""Tests for the $search equals operator."""

from __future__ import annotations

import datetime
import uuid

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
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_MAX,
)

pytestmark = pytest.mark.requires(search=True)


_EQUALS_OBJECT_ID = ObjectId("0123456789abcdef01234567")

_EQUALS_UUID = uuid.UUID("12345678-1234-4567-8901-123456789abc")

_EQUALS_DATE = datetime.datetime(2020, 1, 1)

_EQUALS_DOCS = [
    {"_id": 1, "b": True},
    {"_id": 2, "b": False},
    {"_id": 3, "oid": _EQUALS_OBJECT_ID},
    {"_id": 4, "dt": _EQUALS_DATE},
    {"_id": 5, "s": "apple"},  # stored on a token-mapped path
    {"_id": 6, "nullf": None},
    {"_id": 7, "u": Binary.from_uuid(_EQUALS_UUID)},
    {"_id": 8, "num": 20},  # int32
    {"_id": 9, "num": Int64(20)},  # int64
    {"_id": 10, "num": 20.0},  # double
    {"_id": 11, "big": Int64(DOUBLE_PRECISION_LOSS)},  # 2^53+1 (no exact double)
    {"_id": 12, "big": float(DOUBLE_MAX_SAFE_INTEGER)},  # 2^53
    {"_id": 13, "imax": INT64_MAX},  # int64-max
    {"_id": 14, "imax": DOUBLE_FROM_INT64_MAX},  # int64-max's double approximation
    {"_id": 15, "zero": DOUBLE_ZERO},
    {"_id": 16, "zero": DOUBLE_NEGATIVE_ZERO},
    {"_id": 17, "nf": FLOAT_NAN},
    {"_id": 18, "nf": FLOAT_INFINITY},
    {"_id": 19, "nf": FLOAT_NEGATIVE_INFINITY},
]

_EQUALS_INDEX_DEFINITION = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "b": {"type": "boolean"},
            "oid": {"type": "objectId"},
            "dt": {"type": "date"},
            "s": {"type": "token"},
            "txt": {"type": "string"},
            "nf": {"type": "number"},
            "nullf": {"type": "token"},
            "u": {"type": "uuid"},
            "num": {"type": "number"},
            "big": {"type": "number"},
            "imax": {"type": "number"},
            "zero": {"type": "number"},
        },
    }
}


@pytest.fixture(scope="module")
def equals_collection(engine_client, worker_id):
    """A module-scoped collection with a static search index mapping a field of
    each equals-supported value type (boolean, objectId, date, token string, null,
    uuid, and number), shared read-only across the equals cases so the index is
    built and polled once."""
    db_name = fixtures.generate_database_name("stages_search_equals", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["equals"]
    coll.insert_many(_EQUALS_DOCS)
    create_search_index(coll, _EQUALS_INDEX_DEFINITION)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


# Property [Equals Value-Type Match]: equals returns the document storing a value
# exactly equal to the queried value, for each supported value type.
SEARCH_EQUALS_VALUE_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "equals_bool_true",
        pipeline=[{"$search": {"equals": {"path": "b", "value": True}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search equals should match the document storing the queried boolean true",
    ),
    StageTestCase(
        "equals_bool_false",
        pipeline=[{"$search": {"equals": {"path": "b", "value": False}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 2)]},
        msg="$search equals should match the document storing the queried boolean false",
    ),
    StageTestCase(
        "equals_object_id",
        pipeline=[
            {"$search": {"equals": {"path": "oid", "value": _EQUALS_OBJECT_ID}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 3)]},
        msg="$search equals should match the document storing the queried ObjectId",
    ),
    StageTestCase(
        "equals_date",
        pipeline=[
            {"$search": {"equals": {"path": "dt", "value": _EQUALS_DATE}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 4)]},
        msg="$search equals should match the document storing the queried date",
    ),
    StageTestCase(
        "equals_string_token",
        pipeline=[
            {"$search": {"equals": {"path": "s", "value": "apple"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 5)]},
        msg="$search equals should match the document storing the queried string on a "
        "token-mapped path",
    ),
    StageTestCase(
        "equals_null",
        pipeline=[
            {"$search": {"equals": {"path": "nullf", "value": None}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 6)]},
        msg="$search equals should match the document storing the queried null value",
    ),
    StageTestCase(
        "equals_uuid",
        pipeline=[
            {"$search": {"equals": {"path": "u", "value": Binary.from_uuid(_EQUALS_UUID)}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 7)]},
        msg="$search equals should match the document storing the queried UUID (Binary subtype 4)",
    ),
]

# Property [Equals Lossy Double Numeric Equality]: equals compares numbers in
# double space, so all numeric representations of one value match each other and
# a value with no exact double matches every representation that narrows to the
# same double.
SEARCH_EQUALS_NUMERIC_TESTS: list[StageTestCase] = [
    StageTestCase(
        "equals_int_matches_all_representations",
        pipeline=[{"$search": {"equals": {"path": "num", "value": 20}}}],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 8),
                Contains("_id", 9),
                Contains("_id", 10),
            ]
        },
        msg="$search equals with an int value should match the int32, int64, and double "
        "representations of the same integer",
    ),
    StageTestCase(
        "equals_double_matches_all_representations",
        pipeline=[
            {"$search": {"equals": {"path": "num", "value": 20.0}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 8),
                Contains("_id", 9),
                Contains("_id", 10),
            ]
        },
        msg="$search equals with a double value should match the int32, int64, and double "
        "representations of the same integer",
    ),
    StageTestCase(
        "equals_int64_2pow53_plus_1",
        pipeline=[
            {"$search": {"equals": {"path": "big", "value": Int64(DOUBLE_PRECISION_LOSS)}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 11), Contains("_id", 12)]},
        msg="$search equals with an int64 having no exact double should match both stored "
        "representations that narrow to the same double",
    ),
    StageTestCase(
        "equals_double_2pow53",
        pipeline=[
            {"$search": {"equals": {"path": "big", "value": float(DOUBLE_MAX_SAFE_INTEGER)}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 11), Contains("_id", 12)]},
        msg="$search equals with a double should match both stored representations that "
        "narrow to the same double",
    ),
    StageTestCase(
        "equals_int64_max",
        pipeline=[
            {"$search": {"equals": {"path": "imax", "value": INT64_MAX}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 13), Contains("_id", 14)]},
        msg="$search equals with int64-max should match int64-max and its double approximation",
    ),
]

# Property [Equals Negative Zero]: equals treats negative zero as equal to positive
# zero, so a 0.0 or -0.0 query each matches both a stored 0.0 and a stored -0.0.
SEARCH_EQUALS_NEGATIVE_ZERO_TESTS: list[StageTestCase] = [
    StageTestCase(
        "equals_zero_double_positive",
        pipeline=[
            {"$search": {"equals": {"path": "zero", "value": DOUBLE_ZERO}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 15), Contains("_id", 16)]},
        msg="$search equals with positive-zero double should match both stored 0.0 and -0.0",
    ),
    StageTestCase(
        "equals_zero_double_negative",
        pipeline=[
            {"$search": {"equals": {"path": "zero", "value": DOUBLE_NEGATIVE_ZERO}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 15), Contains("_id", 16)]},
        msg="$search equals with negative-zero double should match both stored 0.0 and -0.0",
    ),
]

# Property [Equals Non-Finite No Match]: equals never matches a stored NaN, +inf,
# or -inf, unlike in which matches them.
SEARCH_EQUALS_NON_FINITE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "equals_nan",
        pipeline=[
            {"$search": {"equals": {"path": "nf", "value": FLOAT_NAN}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search equals should never match a stored NaN",
    ),
    StageTestCase(
        "equals_positive_infinity",
        pipeline=[
            {"$search": {"equals": {"path": "nf", "value": FLOAT_INFINITY}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search equals should never match a stored +inf",
    ),
    StageTestCase(
        "equals_negative_infinity",
        pipeline=[
            {"$search": {"equals": {"path": "nf", "value": FLOAT_NEGATIVE_INFINITY}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search equals should never match a stored -inf",
    ),
]

SEARCH_EQUALS_TESTS = (
    SEARCH_EQUALS_VALUE_TYPE_TESTS
    + SEARCH_EQUALS_NUMERIC_TESTS
    + SEARCH_EQUALS_NEGATIVE_ZERO_TESTS
    + SEARCH_EQUALS_NON_FINITE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_EQUALS_TESTS))
def test_search_equals_cases(equals_collection, test_case: StageTestCase):
    """Test $search equals value semantics across the supported value types."""
    result = execute_command(
        equals_collection,
        {"aggregate": equals_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [Equals Value Type Rejection]: equals.value rejects any type outside
# the supported set (bool, objectId, number, string, date, uuid, null).
SEARCH_EQUALS_VALUE_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"equals_value_type_{tid}",
        pipeline=[{"$search": {"equals": {"path": "num", "value": val}}}],
        error_code=UNKNOWN_ERROR,
        msg=f"$search equals should reject a {tid} value as an unsupported type",
    )
    for tid, val in [
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("timestamp", Timestamp(1, 1)),
        ("array", [1, 2]),
        ("object", {"a": 1}),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Equals Binary Subtype]: a Binary equals.value is accepted only as a
# UUID (subtype 4), so a Binary of any other subtype is rejected.
SEARCH_EQUALS_BINARY_SUBTYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "equals_binary_non_uuid",
        pipeline=[
            {"$search": {"equals": {"path": "u", "value": Binary(b"\x01\x02\x03")}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search equals should reject a Binary value that is not UUID subtype 4",
    ),
]

# Property [Equals Analyzed Path]: a string equals.value requires a token-mapped
# path.
SEARCH_EQUALS_ANALYZED_PATH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "equals_string_analyzed_path",
        pipeline=[
            {"$search": {"equals": {"path": "txt", "value": "quick brown"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search equals should reject a string value against an analyzed non-token path",
    ),
]

SEARCH_EQUALS_ERROR_TESTS = (
    SEARCH_EQUALS_VALUE_TYPE_ERROR_TESTS
    + SEARCH_EQUALS_BINARY_SUBTYPE_ERROR_TESTS
    + SEARCH_EQUALS_ANALYZED_PATH_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_EQUALS_ERROR_TESTS))
def test_search_equals_errors(equals_collection, test_case: StageTestCase):
    """Test $search equals rejects unsupported value types, non-UUID Binary, and analyzed paths."""
    result = execute_command(
        equals_collection,
        {"aggregate": equals_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
