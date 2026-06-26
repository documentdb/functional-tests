"""Tests for the $search in operator."""

from __future__ import annotations

import datetime
import uuid

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.search.utils.search_common import (
    QUERY_CLAUSE_CAP,
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
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

pytestmark = pytest.mark.requires(search=True)


_IN_OBJECT_ID = ObjectId("0123456789abcdef01234567")

_IN_UUID = uuid.UUID("12345678-1234-4567-8901-123456789abc")

_IN_DATE = datetime.datetime(2020, 1, 1)

_IN_DOCS = [
    {"_id": 1, "num": 20},  # int32
    {"_id": 2, "num": Int64(20)},  # int64
    {"_id": 3, "num": 20.0},  # double
    {"_id": 4, "num": 5},  # int32, distinct value
    {"_id": 5, "big": Int64(DOUBLE_PRECISION_LOSS)},  # 2^53+1 (no exact double)
    {"_id": 6, "big": float(DOUBLE_MAX_SAFE_INTEGER)},  # 2^53
    {"_id": 7, "zero": DOUBLE_ZERO},
    {"_id": 8, "zero": DOUBLE_NEGATIVE_ZERO},
    {"_id": 9, "nf": FLOAT_NAN},
    {"_id": 10, "nf": FLOAT_INFINITY},
    {"_id": 11, "nf": FLOAT_NEGATIVE_INFINITY},
    {"_id": 12, "b": True},
    {"_id": 13, "oid": _IN_OBJECT_ID},
    {"_id": 14, "dt": _IN_DATE},
    {"_id": 15, "s": "apple"},  # stored on a token-mapped path
    {"_id": 16, "u": Binary.from_uuid(_IN_UUID)},
]

_IN_INDEX_DEFINITION = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "num": {"type": "number"},
            "big": {"type": "number"},
            "zero": {"type": "number"},
            "nf": {"type": "number"},
            "b": {"type": "boolean"},
            "oid": {"type": "objectId"},
            "dt": {"type": "date"},
            "s": {"type": "token"},
            "u": {"type": "uuid"},
        },
    }
}


@pytest.fixture(scope="module")
def in_collection(engine_client, worker_id):
    """A module-scoped collection with a static search index mapping four
    number-typed fields (mixed numeric representations, a lossy-double pair, a
    signed-zero pair, and the non-finite doubles) plus one field of each other
    supported value type (boolean, objectId, date, token string, and uuid),
    shared read-only across the in cases so the index is built and polled once."""
    db_name = fixtures.generate_database_name("stages_search_in", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["in_op"]
    coll.insert_many(_IN_DOCS)
    create_search_index(coll, _IN_INDEX_DEFINITION)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


# Property [In Value Or Array]: in.value accepts both a single scalar and an
# array, each selecting the documents storing a value equal to a listed value.
SEARCH_IN_VALUE_OR_ARRAY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "in_single_scalar",
        pipeline=[{"$search": {"in": {"path": "num", "value": 20}}}],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
            ]
        },
        msg="$search in should accept a single scalar value and match the documents storing it",
    ),
    StageTestCase(
        "in_array_single_element",
        pipeline=[{"$search": {"in": {"path": "num", "value": [20]}}}],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
            ]
        },
        msg="$search in should accept an array value and match the documents storing a "
        "listed value",
    ),
]

# Property [In Value-Type Acceptance]: like equals, in matches each supported
# non-numeric value type, selecting the document storing a listed value.
SEARCH_IN_VALUE_TYPE_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "in_value_type_bool",
        pipeline=[{"$search": {"in": {"path": "b", "value": [True]}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 12)]},
        msg="$search in should match the document storing a listed boolean value",
    ),
    StageTestCase(
        "in_value_type_objectid",
        pipeline=[{"$search": {"in": {"path": "oid", "value": [_IN_OBJECT_ID]}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 13)]},
        msg="$search in should match the document storing a listed ObjectId value",
    ),
    StageTestCase(
        "in_value_type_date",
        pipeline=[{"$search": {"in": {"path": "dt", "value": [_IN_DATE]}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 14)]},
        msg="$search in should match the document storing a listed date value",
    ),
    StageTestCase(
        "in_value_type_string",
        pipeline=[{"$search": {"in": {"path": "s", "value": ["apple"]}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 15)]},
        msg="$search in should match the document storing a listed string value on a "
        "token-mapped path",
    ),
    StageTestCase(
        "in_value_type_uuid",
        pipeline=[{"$search": {"in": {"path": "u", "value": [Binary.from_uuid(_IN_UUID)]}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 16)]},
        msg="$search in should match the document storing a listed UUID value (Binary subtype 4)",
    ),
]

# Property [In Mixed-Numeric Homogeneity]: in treats int32/int64/double as one
# type, so a mixed-numeric array is accepted and matches every stored numeric
# representation that narrows to a listed value's double, with -0.0 equal to 0.0.
SEARCH_IN_MIXED_NUMERIC_TESTS: list[StageTestCase] = [
    StageTestCase(
        "in_mixed_distinct_values",
        pipeline=[
            {"$search": {"in": {"path": "num", "value": [5, 20.0]}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(4),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search in should accept a mixed-numeric array and match the union of its "
        "listed values",
    ),
    StageTestCase(
        "in_mixed_int64_and_double",
        pipeline=[
            {"$search": {"in": {"path": "num", "value": [Int64(20), 20.0]}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
            ]
        },
        msg="$search in should treat int64 and double as one type in a mixed array and match "
        "every numeric representation of the listed value",
    ),
    StageTestCase(
        "in_lossy_double_equality",
        pipeline=[
            {"$search": {"in": {"path": "big", "value": [Int64(DOUBLE_PRECISION_LOSS)]}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 5), Contains("_id", 6)]},
        msg="$search in should compare in double space, matching both stored representations "
        "that narrow to the same double",
    ),
    StageTestCase(
        "in_negative_zero_positive",
        pipeline=[
            {"$search": {"in": {"path": "zero", "value": [DOUBLE_ZERO]}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 7), Contains("_id", 8)]},
        msg="$search in with positive-zero should match both stored 0.0 and -0.0",
    ),
    StageTestCase(
        "in_negative_zero_negative",
        pipeline=[
            {"$search": {"in": {"path": "zero", "value": [DOUBLE_NEGATIVE_ZERO]}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 7), Contains("_id", 8)]},
        msg="$search in with negative-zero should match both stored 0.0 and -0.0",
    ),
]

# Property [In No Clause Cap]: in imposes no clause cap, so query arrays sized at
# and one past the text.query clause cap are both accepted.
SEARCH_IN_CLAUSE_CAP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "in_clause_count_1024",
        pipeline=[
            {
                "$search": {
                    "in": {
                        "path": "num",
                        "value": [20] + list(range(1000, 1000 + QUERY_CLAUSE_CAP - 1)),
                    }
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
            ]
        },
        msg="$search in should accept a value array sized at the text.query clause cap "
        "with no clause cap of its own",
    ),
    StageTestCase(
        "in_clause_count_1025",
        pipeline=[
            {
                "$search": {
                    "in": {
                        "path": "num",
                        "value": [20] + list(range(1000, 1000 + QUERY_CLAUSE_CAP)),
                    }
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
            ]
        },
        msg="$search in should accept a value array one past the text.query clause cap",
    ),
]

# Property [In Non-Finite Doubles]: in matches a stored NaN, +inf, or -inf when
# that non-finite double is listed, the opposite of equals which never matches
# them.
SEARCH_IN_NON_FINITE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "in_nan",
        pipeline=[
            {"$search": {"in": {"path": "nf", "value": [FLOAT_NAN]}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 9)]},
        msg="$search in should match a stored NaN, unlike equals",
    ),
    StageTestCase(
        "in_positive_infinity",
        pipeline=[
            {"$search": {"in": {"path": "nf", "value": [FLOAT_INFINITY]}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 10)]},
        msg="$search in should match a stored +inf, unlike equals",
    ),
    StageTestCase(
        "in_negative_infinity",
        pipeline=[
            {"$search": {"in": {"path": "nf", "value": [FLOAT_NEGATIVE_INFINITY]}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 11)]},
        msg="$search in should match a stored -inf, unlike equals",
    ),
]

# Property [In doesNotAffect Option]: in recognizes a string doesNotAffect option
# (unlike text or near, which reject the field), accepting it and still returning
# its matches.
SEARCH_IN_DOES_NOT_AFFECT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "in_does_not_affect_string",
        pipeline=[{"$search": {"in": {"path": "b", "value": [True], "doesNotAffect": "score"}}}],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 12)]},
        msg="$search in should accept a string doesNotAffect option and still return its matches",
    ),
]

SEARCH_IN_TESTS = (
    SEARCH_IN_VALUE_OR_ARRAY_TESTS
    + SEARCH_IN_VALUE_TYPE_ACCEPTANCE_TESTS
    + SEARCH_IN_MIXED_NUMERIC_TESTS
    + SEARCH_IN_CLAUSE_CAP_TESTS
    + SEARCH_IN_NON_FINITE_TESTS
    + SEARCH_IN_DOES_NOT_AFFECT_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_IN_TESTS))
def test_search_in_cases(in_collection, test_case: StageTestCase):
    """Test $search in value semantics over a number-mapped path."""
    result = execute_command(
        in_collection,
        {"aggregate": in_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [In Required Fields]: in.path and in.value are both required, so a
# spec omitting either is rejected.
SEARCH_IN_REQUIRED_FIELD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "in_path_missing",
        pipeline=[{"$search": {"in": {"value": [20]}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search in should reject a spec that omits the required path",
    ),
    StageTestCase(
        "in_value_missing",
        pipeline=[{"$search": {"in": {"path": "num"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search in should reject a spec that omits the required value",
    ),
]

# Property [In doesNotAffect Type]: the doesNotAffect option must be a string, so
# a non-string is rejected.
SEARCH_IN_DOES_NOT_AFFECT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "in_does_not_affect_non_string",
        pipeline=[{"$search": {"in": {"path": "num", "value": [20], "doesNotAffect": 1}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search in should reject a non-string doesNotAffect option",
    ),
]

# Property [In Empty Value Array]: an empty in.value array is rejected as it lists
# no value to match.
SEARCH_IN_EMPTY_VALUE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "in_empty_value_array",
        pipeline=[{"$search": {"in": {"path": "num", "value": []}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search in should reject an empty value array",
    ),
]

# Property [In Null Element]: a null element in the in.value array is rejected,
# unlike equals which accepts null.
SEARCH_IN_NULL_ELEMENT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "in_null_element",
        pipeline=[{"$search": {"in": {"path": "num", "value": [None]}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search in should reject a null element in the value array",
    ),
]

# Property [In Element Homogeneity]: every in.value element must share one type
# category, so an array mixing distinct categories is rejected (numeric subtypes
# count as one category).
SEARCH_IN_MIXED_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "in_mixed_number_string",
        pipeline=[
            {"$search": {"in": {"path": "num", "value": [20, "apple"]}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search in should reject an array mixing a number and a string",
    ),
]

# Property [In Element Value Type Dispatch]: in dispatches each in.value array
# element through the same value-type validator as equals.value, so a Binary
# element is accepted only as a UUID (subtype 4).
SEARCH_IN_VALUE_TYPE_ERROR_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"in_value_type_{tid}",
            pipeline=[
                {"$search": {"in": {"path": "num", "value": [val]}}},
            ],
            error_code=UNKNOWN_ERROR,
            msg=f"$search in should route a {tid} element through the value-type validator "
            "and reject it",
        )
        for tid, val in [
            ("decimal128", DECIMAL128_ONE_AND_HALF),
            ("timestamp", Timestamp(1, 1)),
            ("object", {"a": 1}),
            ("nested_array", [1, 2]),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    StageTestCase(
        "in_value_type_binary_non_uuid",
        pipeline=[
            {"$search": {"in": {"path": "u", "value": [Binary(b"\x01\x02\x03")]}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search in should reject a Binary element that is not UUID subtype 4",
    ),
]

SEARCH_IN_ERROR_TESTS = (
    SEARCH_IN_REQUIRED_FIELD_ERROR_TESTS
    + SEARCH_IN_DOES_NOT_AFFECT_ERROR_TESTS
    + SEARCH_IN_EMPTY_VALUE_ERROR_TESTS
    + SEARCH_IN_NULL_ELEMENT_ERROR_TESTS
    + SEARCH_IN_MIXED_TYPE_ERROR_TESTS
    + SEARCH_IN_VALUE_TYPE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_IN_ERROR_TESTS))
def test_search_in_errors(in_collection, test_case: StageTestCase):
    """Test $search in rejects empty, null, mixed-type, and unsupported-type values."""
    result = execute_command(
        in_collection,
        {"aggregate": in_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
