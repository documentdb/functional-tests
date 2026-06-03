"""Tests for $[<identifier>] with data type coverage.

Covers: arrayFilters matching each BSON type, and type coercion behavior.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.array.positional_filtered.utils.filtered_update_test_case import (  # noqa: E501
    FilteredUpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

POSITIONAL_FILTERED_BSON_PARAMS = [
    BsonTypeTestCase(
        id="positional_filtered_update",
        msg="$[<id>] should filter and update elements of this BSON type",
        keyword="positional_filtered",
        valid_types=[bt for bt in BsonType],
    ),
]

ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(POSITIONAL_FILTERED_BSON_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_positional_filtered_bson_types(collection, bson_type, sample_value, spec):
    """Test $[<identifier>] arrayFilters can match and update each BSON type."""
    collection.insert_many([{"_id": 1, "arr": [sample_value, sample_value]}])

    command = {
        "update": collection.name,
        "updates": [
            {
                "q": {"_id": 1},
                "u": {"$set": {"arr.$[elem]": "replaced"}},
                "arrayFilters": [{"elem": sample_value}],
            }
        ],
    }
    result = execute_command(collection, command)
    assertSuccess(
        result,
        {"n": 1, "nModified": 1, "ok": 1.0},
        msg=f"$[<id>] should filter and update {bson_type.value} elements",
        raw_res=True,
    )


TYPE_COERCION_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "mixed_numeric_gt",
        setup_docs=[{"_id": 1, "arr": [1, Int64(2), 3.0, Decimal128("4")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gt": 2}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $gt on mixed numeric types should compare correctly",
    ),
    FilteredUpdateTestCase(
        "negative_zero_matches_zero",
        setup_docs=[{"_id": 1, "arr": [-0.0, 1, 2]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": 0}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] filter on 0 should match -0.0 (negative zero equals zero)",
    ),
    FilteredUpdateTestCase(
        "int_matches_equivalent_double",
        setup_docs=[{"_id": 1, "arr": [1.0, 2.0, 3.0]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": 2}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] int filter should match equivalent double value",
    ),
    FilteredUpdateTestCase(
        "int_matches_equivalent_int64",
        setup_docs=[{"_id": 1, "arr": [Int64(10), Int64(20), Int64(30)]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": 20}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] int32 filter should match equivalent int64 value",
    ),
    FilteredUpdateTestCase(
        "int_matches_equivalent_decimal128",
        setup_docs=[{"_id": 1, "arr": [Decimal128("1"), Decimal128("2"), Decimal128("3")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": 2}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] int filter should match equivalent Decimal128 value",
    ),
    FilteredUpdateTestCase(
        "bool_does_not_match_numeric_one",
        setup_docs=[{"_id": 1, "arr": [True, 1, 2]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": 1}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] numeric 1 should not match bool true (different BSON types)",
    ),
    FilteredUpdateTestCase(
        "bool_does_not_match_numeric_zero",
        setup_docs=[{"_id": 1, "arr": [False, 0, 1]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": 0}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] numeric 0 should not match bool false (different BSON types)",
    ),
    FilteredUpdateTestCase(
        "float_nan_matches_decimal128_nan",
        setup_docs=[{"_id": 1, "arr": [Decimal128("NaN"), 1, 2]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": float("nan")}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] float NaN filter should match Decimal128 NaN",
    ),
    FilteredUpdateTestCase(
        "decimal128_nan_matches_float_nan",
        setup_docs=[{"_id": 1, "arr": [float("nan"), 1, 2]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": Decimal128("NaN")}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] Decimal128 NaN filter should match float NaN",
    ),
    FilteredUpdateTestCase(
        "string_does_not_match_numeric",
        setup_docs=[{"_id": 1, "arr": [5, "5", 10]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": "5"}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with string '5' should match string not numeric 5 (type matters)",
    ),
    FilteredUpdateTestCase(
        "numeric_does_not_match_string",
        setup_docs=[{"_id": 1, "arr": [5, "5", 10]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": 5}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with numeric 5 should match numeric not string '5' (type matters)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TYPE_COERCION_TESTS))
def test_positional_filtered_type_coercion(collection, test: FilteredUpdateTestCase):
    """Test $[<identifier>] type coercion behavior in arrayFilters."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update, "arrayFilters": test.array_filters}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
