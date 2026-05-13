"""Tests for $geoNear syntax validation errors."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Int64, ObjectId, Regex, Timestamp
from bson.decimal128 import Decimal128
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    EXPRESSION_NOT_OBJECT_ERROR,
    GEO_NEAR_NEAR_REQUIRED_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Syntax Validation - Non-Object Spec]: $geoNear rejects all
# non-object spec values.
GEONEAR_SYNTAX_NON_OBJECT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "spec_string",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[{"$geoNear": "hello"}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$geoNear with string spec should fail",
    ),
    StageTestCase(
        "spec_number",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[{"$geoNear": 42}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$geoNear with number spec should fail",
    ),
    StageTestCase(
        "spec_null",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[{"$geoNear": None}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$geoNear with null spec should fail",
    ),
    StageTestCase(
        "spec_bool",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[{"$geoNear": True}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$geoNear with bool spec should fail",
    ),
    StageTestCase(
        "spec_float",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[{"$geoNear": 3.14}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$geoNear with float spec should fail",
    ),
    StageTestCase(
        "spec_int64",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[{"$geoNear": Int64(1)}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$geoNear with Int64 spec should fail",
    ),
    StageTestCase(
        "spec_decimal128",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[{"$geoNear": Decimal128("1")}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$geoNear with Decimal128 spec should fail",
    ),
    StageTestCase(
        "spec_objectid",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[{"$geoNear": ObjectId("000000000000000000000001")}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$geoNear with ObjectId spec should fail",
    ),
    StageTestCase(
        "spec_datetime",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[{"$geoNear": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$geoNear with datetime spec should fail",
    ),
    StageTestCase(
        "spec_timestamp",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[{"$geoNear": Timestamp(1, 1)}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$geoNear with Timestamp spec should fail",
    ),
    StageTestCase(
        "spec_binary",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[{"$geoNear": Binary(b"\x01")}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$geoNear with Binary spec should fail",
    ),
    StageTestCase(
        "spec_regex",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[{"$geoNear": Regex("^a")}],
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="$geoNear with Regex spec should fail",
    ),
]

# Property [Syntax Validation - Array Spec and Missing Near]: when the
# $geoNear spec is an array or the near field is absent from the spec, the
# server rejects it with a near-required error.
GEONEAR_SYNTAX_NEAR_REQUIRED_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "spec_array",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[{"$geoNear": [1, 2]}],
        error_code=GEO_NEAR_NEAR_REQUIRED_ERROR,
        msg="$geoNear with array spec should fail",
    ),
    StageTestCase(
        "near_missing",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_NEAR_REQUIRED_ERROR,
        msg="$geoNear with near missing from spec should fail",
    ),
]

# Property [Syntax Validation - Unrecognized Option]: an unrecognized field
# in the $geoNear spec is rejected.
GEONEAR_SYNTAX_UNRECOGNIZED_OPTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unrecognized_option",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "bogusOption": 1,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear with unrecognized option should fail",
    ),
]

GEONEAR_SYNTAX_ERROR_TESTS = (
    GEONEAR_SYNTAX_NON_OBJECT_ERROR_TESTS
    + GEONEAR_SYNTAX_NEAR_REQUIRED_ERROR_TESTS
    + GEONEAR_SYNTAX_UNRECOGNIZED_OPTION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_SYNTAX_ERROR_TESTS))
def test_geoNear_syntax_errors(collection, test_case: StageTestCase):
    """Test $geoNear syntax validation errors."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
