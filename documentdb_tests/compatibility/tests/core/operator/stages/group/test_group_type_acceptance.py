"""Aggregation $group stage tests - BSON type acceptance in _id."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_SUBNORMAL,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

# Property [Literal BSON Type Acceptance (_id)]: all standard BSON types are
# accepted as literal _id values, object _id values are accepted when fields
# contain non-numeric/non-bool values or are wrapped with $literal, and empty
# object {} groups all documents together and is distinct from null.
GROUP_TYPE_ACCEPTANCE_ID_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="id_int64",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": Int64(42), "count": {"$sum": 1}}}],
        expected=[{"_id": Int64(42), "count": 2}],
        msg="Int64 literal _id should be accepted",
    ),
    StageTestCase(
        id="id_double",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": 3.14, "count": {"$sum": 1}}}],
        expected=[{"_id": 3.14, "count": 2}],
        msg="double literal _id should be accepted",
    ),
    StageTestCase(
        id="id_decimal128",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": Decimal128("3.14"), "count": {"$sum": 1}}}],
        expected=[{"_id": Decimal128("3.14"), "count": 2}],
        msg="Decimal128 literal _id should be accepted",
    ),
    StageTestCase(
        id="id_bool",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": True, "count": {"$sum": 1}}}],
        expected=[{"_id": True, "count": 2}],
        msg="bool literal _id should be accepted",
    ),
    StageTestCase(
        id="id_array",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": [1, "a"], "count": {"$sum": 1}}}],
        expected=[{"_id": [1, "a"], "count": 2}],
        msg="array literal _id should be accepted",
    ),
    StageTestCase(
        id="id_objectid",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": ObjectId("507f1f77bcf86cd799439011"), "count": {"$sum": 1}}}],
        expected=[{"_id": ObjectId("507f1f77bcf86cd799439011"), "count": 2}],
        msg="ObjectId literal _id should be accepted",
    ),
    StageTestCase(
        id="id_datetime",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[
            {"$group": {"_id": datetime(2024, 1, 1, tzinfo=timezone.utc), "count": {"$sum": 1}}}
        ],
        expected=[{"_id": datetime(2024, 1, 1, tzinfo=timezone.utc), "count": 2}],
        msg="datetime literal _id should be accepted",
    ),
    StageTestCase(
        id="id_timestamp",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": Timestamp(1, 1), "count": {"$sum": 1}}}],
        expected=[{"_id": Timestamp(1, 1), "count": 2}],
        msg="Timestamp literal _id should be accepted",
    ),
    StageTestCase(
        id="id_binary",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": Binary(b"data"), "count": {"$sum": 1}}}],
        expected=[{"_id": b"data", "count": 2}],
        msg="Binary literal _id should be accepted",
    ),
    StageTestCase(
        id="id_regex",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": Regex("abc", "i"), "count": {"$sum": 1}}}],
        expected=[{"_id": Regex("abc", "i"), "count": 2}],
        msg="Regex literal _id should be accepted",
    ),
    StageTestCase(
        id="id_code",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": Code("function(){}"), "count": {"$sum": 1}}}],
        expected=[{"_id": Code("function(){}"), "count": 2}],
        msg="Code literal _id should be accepted",
    ),
    StageTestCase(
        id="id_minkey",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": MinKey(), "count": {"$sum": 1}}}],
        expected=[{"_id": MinKey(), "count": 2}],
        msg="MinKey literal _id should be accepted",
    ),
    StageTestCase(
        id="id_maxkey",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": MaxKey(), "count": {"$sum": 1}}}],
        expected=[{"_id": MaxKey(), "count": 2}],
        msg="MaxKey literal _id should be accepted",
    ),
    StageTestCase(
        id="id_object_with_non_numeric_fields",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[
            {"$group": {"_id": {"a": "hello", "b": None, "c": [1, 2]}, "count": {"$sum": 1}}}
        ],
        expected=[{"_id": {"a": "hello", "b": None, "c": [1, 2]}, "count": 2}],
        msg="Object _id with non-numeric/non-bool field values should be accepted",
    ),
    StageTestCase(
        id="id_empty_object",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": {}, "count": {"$sum": 1}}}],
        expected=[{"_id": {}, "count": 2}],
        msg="Empty object {} as _id should group all documents together",
    ),
    StageTestCase(
        id="id_empty_object_distinct_from_null",
        docs=[{"_id": 1, "v": "use_empty"}, {"_id": 2, "v": "use_null"}],
        pipeline=[
            {
                "$group": {
                    "_id": {"$cond": [{"$eq": ["$v", "use_empty"]}, {}, None]},
                    "ids": {"$push": "$_id"},
                }
            }
        ],
        expected=[
            {"_id": {}, "ids": [1]},
            {"_id": None, "ids": [2]},
        ],
        msg="Empty object {} and null should produce separate groups",
    ),
]

# Property [Numeric Boundary Values in _id]: int32, Int64, double, and
# Decimal128 boundary values are accepted as _id and form distinct groups.
GROUP_NUMERIC_BOUNDARY_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="int32_boundary_values",
        docs=[
            {"_id": 1, "v": INT32_MAX},
            {"_id": 2, "v": INT32_MIN},
            {"_id": 3, "v": INT32_MAX_MINUS_1},
            {"_id": 4, "v": INT32_MIN_PLUS_1},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": INT32_MAX, "ids": [1]},
            {"_id": INT32_MIN, "ids": [2]},
            {"_id": INT32_MAX_MINUS_1, "ids": [3]},
            {"_id": INT32_MIN_PLUS_1, "ids": [4]},
        ],
        msg="int32 boundary values should form distinct groups",
    ),
    StageTestCase(
        id="int64_boundary_values",
        docs=[
            {"_id": 1, "v": INT64_MAX},
            {"_id": 2, "v": INT64_MIN},
            {"_id": 3, "v": INT64_MAX_MINUS_1},
            {"_id": 4, "v": INT64_MIN_PLUS_1},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": INT64_MAX, "ids": [1]},
            {"_id": INT64_MIN, "ids": [2]},
            {"_id": INT64_MAX_MINUS_1, "ids": [3]},
            {"_id": INT64_MIN_PLUS_1, "ids": [4]},
        ],
        msg="Int64 boundary values should form distinct groups",
    ),
    StageTestCase(
        id="double_special_values",
        docs=[
            {"_id": 1, "v": DOUBLE_MAX},
            {"_id": 2, "v": DOUBLE_MIN},
            {"_id": 3, "v": DOUBLE_MIN_SUBNORMAL},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": DOUBLE_MAX, "ids": [1]},
            {"_id": DOUBLE_MIN, "ids": [2]},
            {"_id": DOUBLE_MIN_SUBNORMAL, "ids": [3]},
        ],
        msg="Double boundary and subnormal values should be accepted as _id",
    ),
    StageTestCase(
        id="decimal128_extreme_exponents",
        docs=[
            {"_id": 1, "v": DECIMAL128_MIN_POSITIVE},
            {"_id": 2, "v": DECIMAL128_LARGE_EXPONENT},
            {"_id": 3, "v": DECIMAL128_MIN},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": DECIMAL128_MIN_POSITIVE, "ids": [1]},
            {"_id": DECIMAL128_LARGE_EXPONENT, "ids": [2]},
            {"_id": DECIMAL128_MIN, "ids": [3]},
        ],
        msg="Decimal128 extreme exponent values should be preserved exactly",
    ),
    StageTestCase(
        id="decimal128_int64_overflow_separate",
        docs=[
            {"_id": 1, "v": INT64_MAX},
            {"_id": 2, "v": DECIMAL128_INT64_OVERFLOW},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": INT64_MAX, "ids": [1]},
            {"_id": DECIMAL128_INT64_OVERFLOW, "ids": [2]},
        ],
        msg="Decimal128 at Int64 overflow boundary should form a separate group"
        " from the maximum Int64 value",
    ),
]

# Property [Array _id Values]: arrays of any shape are accepted as _id and
# their structure is preserved in the output.
GROUP_ARRAY_ID_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="empty_array_id",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": [], "count": {"$sum": 1}}}],
        expected=[{"_id": [], "count": 2}],
        msg="Empty array [] as _id should group all documents together",
    ),
    StageTestCase(
        id="single_element_array_id",
        docs=[
            {"_id": 1, "v": [10]},
            {"_id": 2, "v": [20]},
            {"_id": 3, "v": [10]},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": [10], "ids": [1, 3]},
            {"_id": [20], "ids": [2]},
        ],
        msg="Single-element array should be accepted as _id",
    ),
    StageTestCase(
        id="multi_element_array_id",
        docs=[
            {"_id": 1, "v": [1, 2, 3]},
            {"_id": 2, "v": [4, 5, 6]},
            {"_id": 3, "v": [1, 2, 3]},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": [1, 2, 3], "ids": [1, 3]},
            {"_id": [4, 5, 6], "ids": [2]},
        ],
        msg="Multi-element array should be accepted as _id",
    ),
    StageTestCase(
        id="nested_array_id",
        docs=[
            {"_id": 1, "v": [[1, 2], [3]]},
            {"_id": 2, "v": [[1, 2], [3]]},
            {"_id": 3, "v": [[1], [2, 3]]},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[
            {"_id": [[1, 2], [3]], "ids": [1, 2]},
            {"_id": [[1], [2, 3]], "ids": [3]},
        ],
        msg="Nested array should be accepted as _id and structure preserved",
    ),
    StageTestCase(
        id="deeply_nested_array_id",
        docs=[
            {"_id": 1, "v": [[[1]]]},
            {"_id": 2, "v": [[[1]]]},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[{"_id": [[[1]]], "ids": [1, 2]}],
        msg="Deeply nested array should be accepted as _id",
    ),
    StageTestCase(
        id="large_array_id",
        docs=[
            {"_id": 1, "v": list(range(150))},
            {"_id": 2, "v": list(range(150))},
        ],
        pipeline=[{"$group": {"_id": "$v", "ids": {"$push": "$_id"}}}],
        expected=[{"_id": list(range(150)), "ids": [1, 2]}],
        msg="Large array (150 elements) should be accepted as _id",
    ),
]


GROUP_TYPE_ACCEPTANCE_TESTS = (
    GROUP_TYPE_ACCEPTANCE_ID_TESTS + GROUP_NUMERIC_BOUNDARY_TESTS + GROUP_ARRAY_ID_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_TYPE_ACCEPTANCE_TESTS))
def test_group_type_acceptance(collection, test_case: StageTestCase):
    """Test $group stage - type acceptance in _id."""
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
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
