"""Tests for $collStats scale factor behavior."""

from __future__ import annotations

from datetime import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, ObjectId, Regex, Timestamp
from bson.max_key import MaxKey
from bson.min_key import MinKey

from documentdb_tests.compatibility.tests.core.operator.stages.collStats.utils.collStats_helpers import (  # noqa: E501
    CollStatsTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import CappedCollection
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_JUST_ABOVE_HALF,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT64_MAX,
)

# Property [Scale Factor Reflected in Output]: the scaleFactor field in the
# output reflects the applied scale value as a BSON int32.
SCALE_FACTOR_REFLECTED_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "scale_1",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": 1}}}],
        checks={"storageStats.scaleFactor": Eq(1)},
        msg="scaleFactor should be 1 with type int32",
    ),
    CollStatsTestCase(
        "scale_2",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": 2}}}],
        checks={"storageStats.scaleFactor": Eq(2)},
        msg="scaleFactor should be 2 with type int32",
    ),
    CollStatsTestCase(
        "scale_7",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": 7}}}],
        checks={"storageStats.scaleFactor": Eq(7)},
        msg="scaleFactor should be 7 with type int32",
    ),
    CollStatsTestCase(
        "scale_1024",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": 1024}}}],
        checks={"storageStats.scaleFactor": Eq(1024)},
        msg="scaleFactor should be 1024 with type int32",
    ),
    CollStatsTestCase(
        "scale_int32_max",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": INT32_MAX}}}],
        checks={"storageStats.scaleFactor": Eq(INT32_MAX)},
        msg="scaleFactor should be INT32_MAX with type int32",
    ),
]

# Property [Scale Factor Clamping to Int32 Max]: all numeric values exceeding
# the int32 maximum are clamped to that limit, including Int64, large doubles,
# large Decimal128, and positive infinity.
SCALE_FACTOR_SUCCESS_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "double_fractional_truncated_down",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": 1.5}}}],
        checks={"storageStats.scaleFactor": Eq(1)},
        msg="scale=1.5 should truncate to scaleFactor=1",
    ),
    CollStatsTestCase(
        "double_large_fraction_truncated",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": 2.9}}}],
        checks={"storageStats.scaleFactor": Eq(2)},
        msg="scale=2.9 should truncate to scaleFactor=2",
    ),
    CollStatsTestCase(
        "double_near_integer_truncated",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": 1023.999}}}],
        checks={"storageStats.scaleFactor": Eq(1023)},
        msg="scale=1023.999 should truncate to scaleFactor=1023",
    ),
    CollStatsTestCase(
        "double_whole_number",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": 3.0}}}],
        checks={"storageStats.scaleFactor": Eq(3)},
        msg="scale=3.0 should produce scaleFactor=3",
    ),
    CollStatsTestCase(
        "decimal128_half_rounds_to_even_2",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": DECIMAL128_ONE_AND_HALF}}}],
        checks={"storageStats.scaleFactor": Eq(2)},
        msg="Decimal128(1.5) should round to scaleFactor=2",
    ),
    CollStatsTestCase(
        "decimal128_half_rounds_to_even_2_again",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": DECIMAL128_TWO_AND_HALF}}}],
        checks={"storageStats.scaleFactor": Eq(2)},
        msg="Decimal128(2.5) should round to scaleFactor=2",
    ),
    CollStatsTestCase(
        "decimal128_half_rounds_to_even_4",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": Decimal128("3.5")}}}],
        checks={"storageStats.scaleFactor": Eq(4)},
        msg="Decimal128(3.5) should round to scaleFactor=4",
    ),
    CollStatsTestCase(
        "decimal128_just_above_half_rounds_to_1",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": DECIMAL128_JUST_ABOVE_HALF}}}],
        checks={"storageStats.scaleFactor": Eq(1)},
        msg="Decimal128 just above 0.5 should round to scaleFactor=1",
    ),
    CollStatsTestCase(
        "int64_just_above_int32_max",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": Int64(INT32_MAX + 1)}}}],
        checks={"storageStats.scaleFactor": Eq(INT32_MAX)},
        msg="Int64 just above int32 max should clamp to int32 max",
    ),
    CollStatsTestCase(
        "int64_max",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": INT64_MAX}}}],
        checks={"storageStats.scaleFactor": Eq(INT32_MAX)},
        msg="Int64 max should clamp to int32 max",
    ),
    CollStatsTestCase(
        "large_double",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": float(10**18)}}}],
        checks={"storageStats.scaleFactor": Eq(INT32_MAX)},
        msg="large double should clamp to int32 max",
    ),
    CollStatsTestCase(
        "positive_infinity_double",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": FLOAT_INFINITY}}}],
        checks={"storageStats.scaleFactor": Eq(INT32_MAX)},
        msg="positive infinity double should clamp to int32 max",
    ),
    CollStatsTestCase(
        "decimal128_just_above_int32_max",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": Decimal128(str(INT32_MAX + 1))}}}],
        checks={"storageStats.scaleFactor": Eq(INT32_MAX)},
        msg="Decimal128 just above int32 max should clamp",
    ),
    CollStatsTestCase(
        "decimal128_large_exponent",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": DECIMAL128_LARGE_EXPONENT}}}],
        checks={"storageStats.scaleFactor": Eq(INT32_MAX)},
        msg="Decimal128 with large exponent should clamp to int32 max",
    ),
    CollStatsTestCase(
        "positive_infinity_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": DECIMAL128_INFINITY}}}],
        checks={"storageStats.scaleFactor": Eq(INT32_MAX)},
        msg="positive infinity Decimal128 should clamp to int32 max",
    ),
]

# Property [Scale Factor Clamping Error]: zero, negative integers, negative
# infinity, NaN (double and Decimal128), Decimal128("-0"), and double -0.0 all
# produce BAD_VALUE_ERROR.
SCALE_FACTOR_ERROR_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "int32_zero",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": 0}}}],
        error_code=BAD_VALUE_ERROR,
        msg="scale=0 should be rejected",
    ),
    CollStatsTestCase(
        "int32_negative_one",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": -1}}}],
        error_code=BAD_VALUE_ERROR,
        msg="scale=-1 should be rejected",
    ),
    CollStatsTestCase(
        "int32_negative_large",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": -100}}}],
        error_code=BAD_VALUE_ERROR,
        msg="scale=-100 should be rejected",
    ),
    CollStatsTestCase(
        "double_positive_fraction",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": 0.5}}}],
        error_code=BAD_VALUE_ERROR,
        msg="scale=0.5 should be rejected (truncates to 0)",
    ),
    CollStatsTestCase(
        "double_negative_fraction",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": -0.5}}}],
        error_code=BAD_VALUE_ERROR,
        msg="scale=-0.5 should be rejected (truncates to 0)",
    ),
    CollStatsTestCase(
        "decimal128_half_rounds_to_zero",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": DECIMAL128_HALF}}}],
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128(0.5) should be rejected (rounds to 0)",
    ),
    CollStatsTestCase(
        "negative_infinity_double",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": FLOAT_NEGATIVE_INFINITY}}}],
        error_code=BAD_VALUE_ERROR,
        msg="negative infinity double should be rejected",
    ),
    CollStatsTestCase(
        "negative_infinity_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": DECIMAL128_NEGATIVE_INFINITY}}}],
        error_code=BAD_VALUE_ERROR,
        msg="negative infinity Decimal128 should be rejected",
    ),
    CollStatsTestCase(
        "nan_double",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": FLOAT_NAN}}}],
        error_code=BAD_VALUE_ERROR,
        msg="NaN double should be rejected",
    ),
    CollStatsTestCase(
        "nan_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": DECIMAL128_NAN}}}],
        error_code=BAD_VALUE_ERROR,
        msg="NaN Decimal128 should be rejected",
    ),
    CollStatsTestCase(
        "decimal128_negative_zero",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": DECIMAL128_NEGATIVE_ZERO}}}],
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128(-0) should be rejected",
    ),
    CollStatsTestCase(
        "double_negative_zero",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": DOUBLE_NEGATIVE_ZERO}}}],
        error_code=BAD_VALUE_ERROR,
        msg="double -0.0 should be rejected",
    ),
]

# Property [storageStats Scale Type Validation Errors]: only numeric types
# (int32, int64, double, Decimal128) and null are accepted for
# storageStats.scale - all non-numeric, non-null types produce
# TYPE_MISMATCH_ERROR.
SCALE_TYPE_ERROR_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        f"scale_{case_id}",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": value}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"storageStats.scale={value!r} should be rejected as non-numeric",
    )
    for value, case_id in [
        ("string", "string"),
        (True, "bool_true"),
        (False, "bool_false"),
        ([1, 2], "array"),
        ({}, "object"),
        (ObjectId(), "objectid"),
        (datetime(2024, 1, 1), "datetime"),
        (Timestamp(0, 0), "timestamp"),
        (Binary(b"x"), "binary"),
        (Regex(".*"), "regex"),
        (Code("function(){}"), "code"),
        (Code("function(){}", {}), "code_with_scope"),
        (MinKey(), "minkey"),
        (MaxKey(), "maxkey"),
    ]
]

COLLSTATS_SCALE_TESTS: list[CollStatsTestCase] = (
    SCALE_FACTOR_REFLECTED_TESTS
    + SCALE_FACTOR_SUCCESS_TESTS
    + SCALE_FACTOR_ERROR_TESTS
    + SCALE_TYPE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(COLLSTATS_SCALE_TESTS))
def test_collStats_scale(database_client, collection, test):
    """Test $collStats scale factor properties."""
    coll = test.prepare(database_client, collection)
    result = execute_command(
        coll, {"aggregate": coll.name, "pipeline": test.pipeline, "cursor": {}}
    )
    test.assert_result(result)


# Property [Scale Factor Divides Size Fields]: specifying storageStats.scale=N
# divides size fields (size, storageSize, totalSize, totalIndexSize, each entry
# in indexSizes) by N using floor division, while avgObjSize, count, nindexes,
# capped, and scaleFactor are unaffected.
SCALE_AFFECTED_FIELDS = [
    "size",
    "storageSize",
    "totalSize",
    "totalIndexSize",
]

SCALE_UNAFFECTED_FIELDS = [
    "avgObjSize",
    "count",
    "nindexes",
    "capped",
    "scaleFactor",
    "indexBuilds",
]


@pytest.mark.aggregate
def test_collStats_scale_divides_size_fields(collection):
    """Test that scale=N floor-divides size fields and leaves others unchanged."""
    collection.insert_many([{"_id": i, "x": "a" * 100} for i in range(50)])
    collection.create_index("x")
    scale = 3
    base = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$collStats": {"storageStats": {}}}],
            "cursor": {},
        },
    )
    scaled = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$collStats": {"storageStats": {"scale": scale}}}],
            "cursor": {},
        },
    )
    if isinstance(base, Exception):
        raise AssertionError(f"unexpected error: {base}")
    b = base["cursor"]["firstBatch"][0]["storageStats"]
    checks: dict[str, Eq] = {"storageStats.nindexes": Eq(2)}
    for field in SCALE_AFFECTED_FIELDS:
        checks[f"storageStats.{field}"] = Eq(int(b[field] // scale))
    for field in SCALE_UNAFFECTED_FIELDS:
        checks[f"storageStats.{field}"] = Eq(scale if field == "scaleFactor" else b[field])
    for key, val in b["indexSizes"].items():
        checks[f"storageStats.indexSizes.{key}"] = Eq(int(val // scale))
    assertProperties(
        scaled,
        checks,
        msg="scale factor should divide size fields and leave others unchanged",
    )


# Property [Scale Factor Capped maxSize]: the maxSize field on a capped
# collection is affected by the scale factor, while max is not.
@pytest.mark.aggregate
def test_collStats_scale_capped_max_size(database_client, collection):
    """Test that scale affects maxSize but not max on capped collections."""
    scale = 4
    capped_coll = CappedCollection(size=1_048_576, max=100).resolve(database_client, collection)
    capped_coll.insert_one({"_id": 1})
    base = execute_command(
        capped_coll,
        {
            "aggregate": capped_coll.name,
            "pipeline": [{"$collStats": {"storageStats": {}}}],
            "cursor": {},
        },
    )
    scaled = execute_command(
        capped_coll,
        {
            "aggregate": capped_coll.name,
            "pipeline": [{"$collStats": {"storageStats": {"scale": scale}}}],
            "cursor": {},
        },
    )
    if isinstance(base, Exception):
        raise AssertionError(f"unexpected error: {base}")
    b = base["cursor"]["firstBatch"][0]["storageStats"]
    assertProperties(
        scaled,
        {
            "storageStats.maxSize": Eq(int(b["maxSize"] // scale)),
            "storageStats.max": Eq(b["max"]),
        },
        msg="scale should affect maxSize but not max",
    )
