"""Tests for $ positional with data type coverage.

Covers: all BSON types as array elements, numeric equivalence in matching,
BSON type distinction, and per-input-position coverage.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertProperties, assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import BsonType

POSITIONAL_BSON_TYPE_SPEC = [
    BsonTypeTestCase(
        id="positional_match",
        msg="$ should match and update array elements of all BSON types",
        keyword="arr",
        valid_types=list(BsonType),
    ),
]

BSON_TYPE_CASES = generate_bson_acceptance_test_cases(POSITIONAL_BSON_TYPE_SPEC)


@pytest.mark.parametrize("bson_type,sample_value,spec", BSON_TYPE_CASES)
def test_positional_bson_types(collection, bson_type, sample_value, spec):
    """Test $ positional matches and updates each BSON type in an array."""
    collection.insert_one({"_id": 1, "arr": [sample_value, sample_value]})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1, "arr": sample_value}, "u": {"$set": {"arr.$": "replaced"}}}
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(result, {"arr.0": Eq("replaced")}, msg=spec.msg)


NUMERIC_EQUIVALENCE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int_matches_long",
        setup_docs=[{"_id": 1, "arr": [Int64(1), Int64(2), Int64(3)]}],
        query={"_id": 1, "arr": 1},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [99, Int64(2), Int64(3)]},
        msg="$ query with int should match long element (numeric equivalence)",
    ),
    UpdateTestCase(
        "double_matches_int",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1, "arr": 1.0},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [99, 2, 3]},
        msg="$ query with double(1.0) should match int(1)",
    ),
    UpdateTestCase(
        "decimal128_matches_int",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1, "arr": Decimal128("1")},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [99, 2, 3]},
        msg="$ query with Decimal128('1') should match int(1)",
    ),
    UpdateTestCase(
        "long_matches_double",
        setup_docs=[{"_id": 1, "arr": [1.0, 2.0, 3.0]}],
        query={"_id": 1, "arr": Int64(2)},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [1.0, 99, 3.0]},
        msg="$ query with long should match double element (numeric equivalence)",
    ),
    UpdateTestCase(
        "negative_zero_matches_zero",
        setup_docs=[{"_id": 1, "arr": [0, 1, 2]}],
        query={"_id": 1, "arr": -0.0},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [99, 1, 2]},
        msg="$ query with -0.0 should match 0 (negative zero equivalence)",
    ),
    UpdateTestCase(
        "null_matches_null",
        setup_docs=[{"_id": 1, "arr": [1, None, 3]}],
        query={"_id": 1, "arr": None},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [1, 99, 3]},
        msg="$ query with null should match null element in array",
    ),
]


BSON_DISTINCTION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "false_not_match_zero",
        setup_docs=[{"_id": 1, "arr": [0, 1, 2]}],
        query={"_id": 1, "arr": False},
        update={"$set": {"arr.$": 99}},
        expected={"n": 0, "nModified": 0, "ok": 1.0},
        msg="$ query with false should NOT match int(0) (distinct BSON types)",
    ),
    UpdateTestCase(
        "true_not_match_one",
        setup_docs=[{"_id": 1, "arr": [0, 1, 2]}],
        query={"_id": 1, "arr": True},
        update={"$set": {"arr.$": 99}},
        expected={"n": 0, "nModified": 0, "ok": 1.0},
        msg="$ query with true should NOT match int(1) (distinct BSON types)",
    ),
    UpdateTestCase(
        "null_not_match_zero",
        setup_docs=[{"_id": 1, "arr": [0, 1, 2]}],
        query={"_id": 1, "arr": None},
        update={"$set": {"arr.$": 99}},
        expected={"n": 0, "nModified": 0, "ok": 1.0},
        msg="$ query with null should NOT match int(0) (distinct BSON types)",
    ),
    UpdateTestCase(
        "string_not_match_int",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1, "arr": "1"},
        update={"$set": {"arr.$": 99}},
        expected={"n": 0, "nModified": 0, "ok": 1.0},
        msg="$ query with string '1' should NOT match int(1) (distinct BSON types)",
    ),
    UpdateTestCase(
        "null_not_match_missing",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1, "arr": None},
        update={"$set": {"arr.$": 99}},
        expected={"n": 0, "nModified": 0, "ok": 1.0},
        msg="$ query with null should NOT match when array has no null element",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NUMERIC_EQUIVALENCE_TESTS))
def test_positional_numeric_equivalence(collection, test: UpdateTestCase):
    """Test $ positional with numeric equivalence across BSON number types."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(BSON_DISTINCTION_TESTS))
def test_positional_bson_type_distinction(collection, test: UpdateTestCase):
    """Test $ positional does not match across distinct BSON types."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
