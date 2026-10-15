"""
Error case tests for $inc update field operator.

Tests conflict detection, dollar-prefixed field restrictions,
and int64 overflow/underflow errors.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CONFLICTING_UPDATE_OPERATORS_ERROR,
    DOLLAR_PREFIXED_FIELD_NAME_ERROR,
    FAILED_TO_PARSE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_MAX, INT64_MIN

# Property [Conflict Detection]: $inc conflicts with other operators on same field or path.
CONFLICT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "inc_and_set_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": 1}, "$set": {"val": 10}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$inc should reject conflict with $set on same field",
    ),
    UpdateTestCase(
        "inc_and_mul_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": 1}, "$mul": {"val": 2}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$inc should reject conflict with $mul on same field",
    ),
    UpdateTestCase(
        "inc_path_prefix_conflict",
        setup_docs=[{"_id": 1, "x": {"y": 5}}],
        query={"_id": 1},
        update={"$inc": {"x.y": 1}, "$set": {"x": {}}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$inc should reject path prefix conflict with $set on parent",
    ),
]

# Property [Dollar-Prefixed Fields]: $inc rejects dollar-prefixed field names.
DOLLAR_PREFIX_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "dollar_prefixed_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"$field": 5}},
        error_code=DOLLAR_PREFIXED_FIELD_NAME_ERROR,
        msg="$inc should reject dollar-prefixed field name",
    ),
    UpdateTestCase(
        "bare_dollar_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"$": 5}},
        error_code=BAD_VALUE_ERROR,
        msg="$inc should reject bare '$' as field name",
    ),
]

# Property [Int64 Overflow]: $inc produces an error when int64 result exceeds int64 range.
INT64_OVERFLOW_ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int64_max_plus_1_int32",
        setup_docs=[{"_id": 1, "val": INT64_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": 1}},
        error_code=BAD_VALUE_ERROR,
        msg="$inc should error on INT64_MAX + int32(1) overflow",
    ),
    UpdateTestCase(
        "int64_max_plus_1_int64",
        setup_docs=[{"_id": 1, "val": INT64_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": Int64(1)}},
        error_code=BAD_VALUE_ERROR,
        msg="$inc should error on INT64_MAX + int64(1) overflow",
    ),
    UpdateTestCase(
        "int64_min_minus_1_int32",
        setup_docs=[{"_id": 1, "val": INT64_MIN}],
        query={"_id": 1},
        update={"$inc": {"val": -1}},
        error_code=BAD_VALUE_ERROR,
        msg="$inc should error on INT64_MIN - int32(1) underflow",
    ),
    UpdateTestCase(
        "int64_min_minus_1_int64",
        setup_docs=[{"_id": 1, "val": INT64_MIN}],
        query={"_id": 1},
        update={"$inc": {"val": Int64(-1)}},
        error_code=BAD_VALUE_ERROR,
        msg="$inc should error on INT64_MIN - int64(1) underflow",
    ),
]

# Property [Operand Type]: $inc requires a document operand; non-document operands fail to parse.
OPERAND_TYPE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "operand_null",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$inc": None},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$inc should fail to parse when operand is null",
    ),
    UpdateTestCase(
        "operand_array",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$inc": [1, 2]},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$inc should fail to parse when operand is an array",
    ),
    UpdateTestCase(
        "operand_string",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$inc": "5"},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$inc should fail to parse when operand is a string",
    ),
    UpdateTestCase(
        "operand_bool",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$inc": True},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$inc should fail to parse when operand is a bool",
    ),
    UpdateTestCase(
        "operand_integer",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$inc": 42},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$inc should fail to parse when operand is an integer",
    ),
]

ALL_ERROR_TESTS = (
    CONFLICT_TESTS + DOLLAR_PREFIX_TESTS + INT64_OVERFLOW_ERROR_TESTS + OPERAND_TYPE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_inc_errors(collection, test: UpdateTestCase):
    """Test $inc error cases produce expected error codes."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)
