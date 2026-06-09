"""Tests for $sort update modifier data type behavior.

Covers: sort spec type validation, BSON type sort ordering, numeric equivalence
across types, null/missing field handling, NaN/Infinity positioning,
Decimal128 precision, and BSON type distinction (false ≠ 0, true ≠ 1).
"""

import math
from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertResult,
    assertSuccess,
)
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# --- Sort spec type validation (framework + manual) ---

SORT_SPEC_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="sort_spec_value",
        msg="$sort spec value type",
        keyword="$sort",
        valid_types=[],
        skip_rejection_types=[
            BsonType.INT,
            BsonType.LONG,
            BsonType.DOUBLE,
            BsonType.DECIMAL,
            BsonType.OBJECT,
        ],
        default_error_code=BAD_VALUE_ERROR,
    ),
]

SORT_SPEC_REJECTION_CASES = generate_bson_rejection_test_cases(SORT_SPEC_TYPE_PARAMS)

SORT_VALUE_VALIDATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="sort_direction_zero",
        setup_docs=[{"_id": 1, "arr": [3, 1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 0}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort: 0 should fail with BadValue",
    ),
    UpdateTestCase(
        id="sort_direction_two",
        setup_docs=[{"_id": 1, "arr": [3, 1, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 2}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort: 2 should fail with BadValue",
    ),
    UpdateTestCase(
        id="sort_field_direction_zero",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"a": 0}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort: {a: 0} should fail with BadValue",
    ),
    UpdateTestCase(
        id="sort_field_direction_string",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"a": "asc"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort: {a: 'asc'} should fail with BadValue",
    ),
    UpdateTestCase(
        id="sort_empty_object",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort: {} (empty object) should fail with BadValue",
    ),
    UpdateTestCase(
        id="sort_trailing_dot_key",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"a.": 1}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort with trailing dot in key path should fail",
    ),
    UpdateTestCase(
        id="sort_empty_string_key",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"": 1}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$sort with empty string key should fail",
    ),
]

NUMERIC_EQUIVALENCE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="doubles_sort_ascending",
        setup_docs=[{"_id": 1, "arr": [3.5, 1.2, 4.8, 2.1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [1.2, 2.1, 3.5, 4.8]}],
        msg="Array of doubles should sort numerically ascending",
    ),
    UpdateTestCase(
        id="cross_type_numeric_sort",
        setup_docs=[{"_id": 1, "arr": [Int64(3), 1, 2.0, Decimal128("4")]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [1, 2.0, Int64(3), Decimal128("4")]}],
        msg="Cross-type numeric values should sort by numeric value",
    ),
    UpdateTestCase(
        id="cross_type_numeric_document_sort",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"val": Int64(3)},
                    {"val": 1.0},
                    {"val": 2},
                    {"val": Decimal128("4")},
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"val": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    {"val": 1.0},
                    {"val": 2},
                    {"val": Int64(3)},
                    {"val": Decimal128("4")},
                ],
            }
        ],
        msg="Document sort should order mixed numeric types by value",
    ),
]

NULL_MISSING_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="null_elements_sort_first",
        setup_docs=[{"_id": 1, "arr": [3, None, 1, None, 2]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [None, None, 1, 2, 3]}],
        msg="Null values should sort before numbers per BSON order",
    ),
    UpdateTestCase(
        id="missing_field_sorts_first",
        setup_docs=[
            {
                "_id": 1,
                "arr": [{"field": 3}, {"name": "no field"}, {"field": 1}],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"field": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [{"name": "no field"}, {"field": 1}, {"field": 3}],
            }
        ],
        msg="Documents with missing sort field should sort first (treated as null)",
    ),
]

NAN_INFINITY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="nan_sorts_before_numbers",
        setup_docs=[{"_id": 1, "arr": [1, FLOAT_NAN, 2, -1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [pytest.approx(math.nan, nan_ok=True), -1, 1, 2]}],
        msg="NaN should sort before all finite numbers",
    ),
    UpdateTestCase(
        id="infinity_sort_order",
        setup_docs=[{"_id": 1, "arr": [FLOAT_NEGATIVE_INFINITY, 0, FLOAT_INFINITY]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [FLOAT_NEGATIVE_INFINITY, 0, FLOAT_INFINITY]}],
        msg="-Infinity < finite numbers < Infinity",
    ),
    UpdateTestCase(
        id="nan_infinity_combined",
        setup_docs=[
            {
                "_id": 1,
                "arr": [1, FLOAT_NAN, FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY, 0],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    pytest.approx(math.nan, nan_ok=True),
                    FLOAT_NEGATIVE_INFINITY,
                    0,
                    1,
                    FLOAT_INFINITY,
                ],
            }
        ],
        msg="NaN < -Infinity < finite numbers < Infinity",
    ),
    UpdateTestCase(
        id="nan_descending",
        setup_docs=[{"_id": 1, "arr": [1, FLOAT_NAN, FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": -1}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    FLOAT_INFINITY,
                    1,
                    FLOAT_NEGATIVE_INFINITY,
                    pytest.approx(math.nan, nan_ok=True),
                ],
            }
        ],
        msg="Descending: Infinity > finite > -Infinity > NaN",
    ),
    UpdateTestCase(
        id="decimal128_nan_groups_with_float_nan",
        setup_docs=[{"_id": 1, "arr": [DECIMAL128_NAN, 1, FLOAT_NAN, Decimal128("2")]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    DECIMAL128_NAN,
                    pytest.approx(math.nan, nan_ok=True),
                    1,
                    Decimal128("2"),
                ],
            }
        ],
        msg="Decimal128 NaN and float NaN should group together before numbers",
    ),
]

DECIMAL128_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="decimal128_sort_order",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    Decimal128("100"),
                    Decimal128("1"),
                    Decimal128("50"),
                    Decimal128("10"),
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    Decimal128("1"),
                    Decimal128("10"),
                    Decimal128("50"),
                    Decimal128("100"),
                ],
            }
        ],
        msg="Decimal128 values should sort by numeric value",
    ),
    UpdateTestCase(
        id="decimal128_document_sort",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"val": Decimal128("100")},
                    {"val": Decimal128("1")},
                    {"val": Decimal128("50")},
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"val": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    {"val": Decimal128("1")},
                    {"val": Decimal128("50")},
                    {"val": Decimal128("100")},
                ],
            }
        ],
        msg="Document sort by Decimal128 field should order correctly",
    ),
]

BSON_TYPE_DISTINCTION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="bool_distinct_from_numbers",
        setup_docs=[{"_id": 1, "arr": [False, 0, True, 1]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [0, 1, False, True]}],
        msg="Numbers should sort before booleans per BSON type order",
    ),
    UpdateTestCase(
        id="distinct_types_document_sort",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"field": None},
                    {"field": 0},
                    {"field": False},
                    {"field": ""},
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"field": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    {"field": None},
                    {"field": 0},
                    {"field": ""},
                    {"field": False},
                ],
            }
        ],
        msg="Distinct BSON types should sort by BSON type order: null < number < string < bool",
    ),
]

MIXED_BSON_TYPE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="mixed_bson_types_sort",
        setup_docs=[{"_id": 1, "arr": [1, "string", None, True, {"a": 1}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [None, 1, "string", {"a": 1}, True]}],
        msg="Mixed BSON types should sort by BSON comparison order",
    ),
    UpdateTestCase(
        id="non_document_elements_with_document_sort",
        setup_docs=[{"_id": 1, "arr": [{"score": 5}, 3, {"score": 1}, "text"]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"score": 1}}}},
        expected=[{"_id": 1, "arr": [3, "text", {"score": 1}, {"score": 5}]}],
        msg="Non-document elements with document sort should sort by BSON type",
    ),
    UpdateTestCase(
        id="sort_array_of_arrays",
        setup_docs=[{"_id": 1, "arr": [[3, 1], [1, 2], [2, 3]]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[{"_id": 1, "arr": [[1, 2], [2, 3], [3, 1]]}],
        msg="Array of arrays should sort by array comparison rules",
    ),
]

DOCUMENT_FIELD_TYPE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="document_sort_by_double_field",
        setup_docs=[{"_id": 1, "arr": [{"val": 3.5}, {"val": 1.2}, {"val": 2.8}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"val": 1}}}},
        expected=[{"_id": 1, "arr": [{"val": 1.2}, {"val": 2.8}, {"val": 3.5}]}],
        msg="Document sort by double field should order correctly",
    ),
    UpdateTestCase(
        id="document_sort_by_long_field",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"val": Int64(300)},
                    {"val": Int64(100)},
                    {"val": Int64(200)},
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"val": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    {"val": Int64(100)},
                    {"val": Int64(200)},
                    {"val": Int64(300)},
                ],
            }
        ],
        msg="Document sort by Int64 field should order correctly",
    ),
    UpdateTestCase(
        id="document_sort_by_string_field",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"val": "cherry"},
                    {"val": "apple"},
                    {"val": "banana"},
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"val": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    {"val": "apple"},
                    {"val": "banana"},
                    {"val": "cherry"},
                ],
            }
        ],
        msg="Document sort by string field should order lexicographically",
    ),
    UpdateTestCase(
        id="document_sort_by_bool_field",
        setup_docs=[{"_id": 1, "arr": [{"val": True}, {"val": False}, {"val": True}]}],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"val": 1}}}},
        expected=[{"_id": 1, "arr": [{"val": False}, {"val": True}, {"val": True}]}],
        msg="Document sort by bool field should order false before true",
    ),
    UpdateTestCase(
        id="document_sort_by_date_field",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    {"val": datetime(2024, 6, 1, tzinfo=timezone.utc)},
                    {"val": datetime(2020, 1, 1, tzinfo=timezone.utc)},
                    {"val": datetime(2022, 3, 15, tzinfo=timezone.utc)},
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": {"val": 1}}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    {"val": datetime(2020, 1, 1, tzinfo=timezone.utc)},
                    {"val": datetime(2022, 3, 15, tzinfo=timezone.utc)},
                    {"val": datetime(2024, 6, 1, tzinfo=timezone.utc)},
                ],
            }
        ],
        msg="Document sort by date field should order chronologically",
    ),
]

DATE_SORT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="dates_sort_chronologically",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    datetime(2024, 6, 1, tzinfo=timezone.utc),
                    datetime(2020, 1, 1, tzinfo=timezone.utc),
                    datetime(2022, 3, 15, tzinfo=timezone.utc),
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": 1}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    datetime(2020, 1, 1, tzinfo=timezone.utc),
                    datetime(2022, 3, 15, tzinfo=timezone.utc),
                    datetime(2024, 6, 1, tzinfo=timezone.utc),
                ],
            }
        ],
        msg="Dates should sort chronologically (earliest first)",
    ),
    UpdateTestCase(
        id="dates_sort_descending",
        setup_docs=[
            {
                "_id": 1,
                "arr": [
                    datetime(2024, 6, 1, tzinfo=timezone.utc),
                    datetime(2020, 1, 1, tzinfo=timezone.utc),
                    datetime(2022, 3, 15, tzinfo=timezone.utc),
                ],
            }
        ],
        query={"_id": 1},
        update={"$push": {"arr": {"$each": [], "$sort": -1}}},
        expected=[
            {
                "_id": 1,
                "arr": [
                    datetime(2024, 6, 1, tzinfo=timezone.utc),
                    datetime(2022, 3, 15, tzinfo=timezone.utc),
                    datetime(2020, 1, 1, tzinfo=timezone.utc),
                ],
            }
        ],
        msg="Dates should sort reverse chronologically (latest first)",
    ),
]


ALL_DATA_TYPE_TESTS = (
    NUMERIC_EQUIVALENCE_TESTS
    + NULL_MISSING_TESTS
    + NAN_INFINITY_TESTS
    + DECIMAL128_TESTS
    + BSON_TYPE_DISTINCTION_TESTS
    + MIXED_BSON_TYPE_TESTS
    + DOCUMENT_FIELD_TYPE_TESTS
    + DATE_SORT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ALL_DATA_TYPE_TESTS))
def test_update_sort_data_types(collection, test_case):
    """Test $sort data type behavior."""
    collection.insert_many(test_case.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test_case.query})
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", SORT_SPEC_REJECTION_CASES)
def test_update_sort_spec_type_rejected(collection, bson_type, sample_value, spec):
    """Test $sort rejects invalid BSON types as sort spec value."""
    collection.insert_one({"_id": 1, "arr": [3, 1, 2]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"arr": {"$each": [], "$sort": sample_value}}},
                }
            ],
        },
    )
    assertFailureCode(
        result,
        spec.expected_code(bson_type),
        msg=f"{spec.msg} should reject {bson_type.value}",
    )


@pytest.mark.parametrize("test_case", pytest_params(SORT_VALUE_VALIDATION_TESTS))
def test_update_sort_value_validation(collection, test_case):
    """Test $sort rejects invalid values within conditionally-valid types."""
    collection.insert_many(test_case.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test_case.query, "u": test_case.update}],
        },
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
