"""Tests for the $search near operator."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

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
    Eq,
    Gt,
    Len,
    PerDoc,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    INT64_MAX,
)

pytestmark = pytest.mark.requires(search=True)


_NEAR_DOCS = [
    {"_id": 1, "num": 0},
    {"_id": 2, "num": 10},
    {"_id": 3, "num": 40},
    {"_id": 4, "dt": datetime.datetime(2020, 1, 1)},
    {"_id": 5, "dt": datetime.datetime(2020, 1, 11)},
    {"_id": 6, "dt": datetime.datetime(2020, 2, 10)},
    {"_id": 7, "loc": {"type": "Point", "coordinates": [DOUBLE_ZERO, DOUBLE_ZERO]}},
    {"_id": 8, "loc": {"type": "Point", "coordinates": [DOUBLE_ZERO, 0.1]}},
    {"_id": 9, "loc": {"type": "Point", "coordinates": [DOUBLE_ZERO, 1.0]}},
    {"_id": 10, "big": INT64_MAX},
    {"_id": 11, "big": DOUBLE_FROM_INT64_MAX},
    {"_id": 12, "big": 5},
]

_NEAR_INDEX_DEFINITION = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "num": {"type": "number"},
            "dt": {"type": "date"},
            "loc": {"type": "geo"},
            "big": {"type": "number"},
        },
    }
}


@pytest.fixture(scope="module")
def near_collection(engine_client, worker_id):
    """A module-scoped collection with a static search index mapping a numeric, a
    date, a geo, and a second numeric (cross-type) field, shared read-only across
    the near cases so the index is built and polled once."""
    db_name = fixtures.generate_database_name("stages_search_near", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["near_op"]
    coll.insert_many(_NEAR_DOCS)
    create_search_index(coll, _NEAR_INDEX_DEFINITION)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


# Property [Near Proximity Ordering]: near orders the documents on the queried
# path by ascending distance from a numeric, date, or geo origin (closest first),
# scoring a document at the exact origin 1.0 and scaling the rest by
# pivot/(pivot+distance).
SEARCH_NEAR_PROXIMITY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "near_numeric_proximity",
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": 10, "pivot": 10}}},
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected=PerDoc(
            {"_id": Eq(2), "score": Eq(1.0)},
            {"_id": Eq(1), "score": Eq(0.5)},
            {"_id": Eq(3), "score": Eq(0.25)},
        ),
        msg="$search near should order numeric results by proximity and score them by "
        "pivot/(pivot+distance)",
    ),
    StageTestCase(
        "near_score_boost",
        pipeline=[
            {
                "$search": {
                    "near": {
                        "path": "num",
                        "origin": 10,
                        "pivot": 10,
                        "score": {"boost": {"value": 2.0}},
                    }
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected=PerDoc(
            {"_id": Eq(2), "score": Gt(0)},
            {"_id": Eq(1), "score": Gt(0)},
            {"_id": Eq(3), "score": Gt(0)},
        ),
        msg="$search near should accept a score modifier and still order its matches by "
        "proximity",
    ),
    StageTestCase(
        "near_date_proximity",
        # The pivot is 10 days expressed in milliseconds, the distance unit for a
        # date origin, so the docs 10 and 30 days away score 0.5 and 0.25.
        pipeline=[
            {
                "$search": {
                    "near": {
                        "path": "dt",
                        "origin": datetime.datetime(2020, 1, 11),
                        "pivot": 864_000_000,
                    }
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected=PerDoc(
            {"_id": Eq(5), "score": Eq(1.0)},
            {"_id": Eq(4), "score": Eq(0.5)},
            {"_id": Eq(6), "score": Eq(0.25)},
        ),
        msg="$search near should order date results by proximity and score them by "
        "pivot/(pivot+distance)",
    ),
    StageTestCase(
        "near_geo_proximity",
        pipeline=[
            {
                "$search": {
                    "near": {
                        "path": "loc",
                        "origin": {"type": "Point", "coordinates": [DOUBLE_ZERO, DOUBLE_ZERO]},
                        "pivot": 10_000,
                    }
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected=PerDoc(
            {"_id": Eq(7), "score": Eq(1.0)},
            {"_id": Eq(8), "score": Gt(0)},
            {"_id": Eq(9), "score": Gt(0)},
        ),
        msg="$search near should order geo results by geodesic proximity and score a "
        "document at the exact origin 1.0",
    ),
]

# Property [Near Pivot Acceptance]: any positive finite pivot is accepted and
# tunes the proximity falloff.
SEARCH_NEAR_PIVOT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "near_pivot_fractional",
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": 10, "pivot": 0.5}}},
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected=PerDoc(
            {"_id": Eq(2), "score": Eq(1.0)},
            {"_id": Eq(1), "score": Gt(0)},
            {"_id": Eq(3), "score": Gt(0)},
        ),
        msg="$search near should accept a fractional pivot and still score the "
        "exact-origin document 1.0",
    ),
    StageTestCase(
        "near_pivot_very_large",
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": 10, "pivot": DOUBLE_MAX}}},
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected={"score": Eq(1.0)},
        msg="$search near should accept a very large pivot, saturating every score to 1.0",
    ),
    StageTestCase(
        "near_pivot_very_small",
        # A 1e-300 pivot underflows pivot/(pivot+distance) to 0.0 for any nonzero
        # distance, so only the exact-origin document keeps a 1.0 score.
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": 10, "pivot": 1e-300}}},
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected=PerDoc(
            {"_id": Eq(2), "score": Eq(1.0)},
            {"score": Eq(DOUBLE_ZERO)},
            {"score": Eq(DOUBLE_ZERO)},
        ),
        msg="$search near should accept a very small pivot, scoring only the "
        "exact-origin document 1.0 and decaying the rest to 0.0",
    ),
]

# Property [Near Numeric Origin Boundaries]: non-finite and extreme numeric
# origins execute without error.
SEARCH_NEAR_ORIGIN_BOUNDARY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "near_origin_nan",
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": FLOAT_NAN, "pivot": 10}}},
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected={"score": Eq(DOUBLE_ZERO)},
        msg="$search near should execute a NaN origin with no error, scoring every document 0.0",
    ),
    StageTestCase(
        "near_origin_infinite",
        # The sign of an infinite-magnitude origin is erased by the absolute
        # distance, so a single infinite-origin case covers both signs.
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": FLOAT_INFINITY, "pivot": 10}}},
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected={"score": Eq(DOUBLE_ZERO)},
        msg="$search near should execute an infinite origin with no error, scoring every "
        "document 0.0",
    ),
    StageTestCase(
        "near_origin_double_max",
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": DOUBLE_MAX, "pivot": 10}}},
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected={"score": Eq(DOUBLE_ZERO)},
        msg="$search near should execute a DBL_MAX origin with no error, scoring every "
        "document 0.0",
    ),
    StageTestCase(
        "near_origin_int64_max_cross_type",
        pipeline=[
            {"$search": {"near": {"path": "big", "origin": INT64_MAX, "pivot": 1}}},
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected=PerDoc(
            {"score": Eq(1.0)},
            {"score": Eq(1.0)},
            {"_id": Eq(12), "score": Gt(0)},
        ),
        msg="$search near should score both the int64-max document and its double "
        "approximation 1.0 for an int64-max origin",
    ),
    StageTestCase(
        "near_origin_negative_zero",
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": DOUBLE_NEGATIVE_ZERO, "pivot": 10}}},
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected=PerDoc(
            {"_id": Eq(1), "score": Eq(1.0)},
            {"_id": Eq(2), "score": Eq(0.5)},
            {"_id": Eq(3), "score": Gt(0)},
        ),
        msg="$search near should treat a -0.0 origin identically to 0.0, scoring the "
        "zero-valued document 1.0",
    ),
]

SEARCH_NEAR_CASES_TESTS = (
    SEARCH_NEAR_PROXIMITY_TESTS + SEARCH_NEAR_PIVOT_TESTS + SEARCH_NEAR_ORIGIN_BOUNDARY_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_NEAR_CASES_TESTS))
def test_search_near_cases(near_collection, test_case: StageTestCase):
    """Test $search near proximity ordering, scoring, pivot, and origin boundaries."""
    result = execute_command(
        near_collection,
        {"aggregate": near_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)


# Property [Near Type-Mismatched Origin Silent No-Match]: a numeric origin against
# a date path returns no documents and no error, unlike the string, null, or
# Decimal128 origins that fail.
SEARCH_NEAR_SILENT_NO_MATCH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "near_numeric_origin_date_path",
        pipeline=[
            {"$search": {"near": {"path": "dt", "origin": 10, "pivot": 10}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search near should return no documents and no error for a numeric origin "
        "on a date path",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_NEAR_SILENT_NO_MATCH_TESTS))
def test_search_near_silent_no_match(near_collection, test_case: StageTestCase):
    """Test $search near returns a silent empty result for a type-mismatched origin."""
    result = execute_command(
        near_collection,
        {"aggregate": near_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [Near Pivot Validation]: near.pivot must be a positive finite number,
# so a non-positive, non-finite, or non-number pivot is rejected.
SEARCH_NEAR_PIVOT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "near_pivot_zero",
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": 10, "pivot": 0}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search near should reject a pivot of zero as not positive",
    ),
    StageTestCase(
        "near_pivot_negative",
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": 10, "pivot": -1}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search near should reject a negative pivot as not positive",
    ),
    StageTestCase(
        "near_pivot_nan",
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": 10, "pivot": FLOAT_NAN}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search near should reject a NaN pivot as not finite",
    ),
    StageTestCase(
        "near_pivot_infinity",
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": 10, "pivot": FLOAT_INFINITY}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search near should reject an infinite pivot as not finite",
    ),
    StageTestCase(
        "near_pivot_non_number",
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": 10, "pivot": "ten"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search near should reject a non-number pivot",
    ),
]

# Property [Near Origin Type Match]: a near.origin of any type outside the
# supported set (number, date, geo Point) is rejected, unlike a type-mismatched
# numeric origin which silently matches nothing.
SEARCH_NEAR_ORIGIN_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"near_origin_{tid}",
        pipeline=[
            {"$search": {"near": {"path": "num", "origin": val, "pivot": 10}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$search near should reject a {tid} origin as an unsupported type",
    )
    for tid, val in [
        ("string", "ten"),
        ("bool", True),
        ("array", [1, 2]),
        ("objectid", ObjectId("0123456789abcdef01234567")),
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

# Property [Near Required Fields]: near.path, near.origin, and near.pivot are all
# required, so a spec omitting any one of them is rejected.
SEARCH_NEAR_REQUIRED_FIELD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "near_path_missing",
        pipeline=[{"$search": {"near": {"origin": 10, "pivot": 10}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search near should reject a spec that omits the required path",
    ),
    StageTestCase(
        "near_origin_missing",
        pipeline=[{"$search": {"near": {"path": "num", "pivot": 10}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search near should reject a spec that omits the required origin",
    ),
    StageTestCase(
        "near_pivot_missing",
        pipeline=[{"$search": {"near": {"path": "num", "origin": 10}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search near should reject a spec that omits the required pivot",
    ),
]

SEARCH_NEAR_ERROR_TESTS = (
    SEARCH_NEAR_PIVOT_ERROR_TESTS
    + SEARCH_NEAR_ORIGIN_TYPE_ERROR_TESTS
    + SEARCH_NEAR_REQUIRED_FIELD_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_NEAR_ERROR_TESTS))
def test_search_near_errors(near_collection, test_case: StageTestCase):
    """Test $search near rejects invalid pivot values and type-mismatched origins."""
    result = execute_command(
        near_collection,
        {"aggregate": near_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
