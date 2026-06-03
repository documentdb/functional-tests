"""Tests for $[] positional-all with data type coverage.

Covers: all BSON types via bson_type_validator framework, numeric equivalence,
and mixed type arrays.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccess
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import BsonType

POSITIONAL_ALL_BSON_TYPE_SPEC = [
    BsonTypeTestCase(
        id="positional_all_update",
        msg="$[] should update all array elements of all BSON types",
        keyword="arr",
        valid_types=list(BsonType),
    ),
]

BSON_TYPE_CASES = generate_bson_acceptance_test_cases(POSITIONAL_ALL_BSON_TYPE_SPEC)


@pytest.mark.parametrize("bson_type,sample_value,spec", BSON_TYPE_CASES)
def test_positional_all_bson_types(collection, bson_type, sample_value, spec):
    """Test $[] positional-all updates each BSON type in an array."""
    collection.insert_one({"_id": 1, "arr": [sample_value, sample_value]})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"arr.$[]": "replaced"}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(result, {"arr.0": Eq("replaced"), "arr.1": Eq("replaced")}, msg=spec.msg)


NUMERIC_EQUIVALENCE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "mixed_numeric_types_all_updated",
        setup_docs=[{"_id": 1, "arr": [1, Int64(2), 3.0, Decimal128("4")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 0}},
        expected={"_id": 1, "arr": [0, 0, 0, 0]},
        msg="$[] should update all elements regardless of numeric subtype",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NUMERIC_EQUIVALENCE_TESTS))
def test_positional_all_numeric_and_null(collection, test: UpdateTestCase):
    """Test $[] positional-all with numeric equivalence and null replacement."""
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
