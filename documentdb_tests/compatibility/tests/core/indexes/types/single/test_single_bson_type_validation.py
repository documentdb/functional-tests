"""Tests for single field index key sort order BSON type validation.

Verifies that single field index key values (sort order specifiers) reject
invalid BSON types and accept valid numeric types.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertNotError
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import CANNOT_CREATE_INDEX_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index

SINGLE_KEY_SORT_ORDER_PARAMS = [
    BsonTypeTestCase(
        id="sort_order",
        msg="single key sort order should reject non-numeric types",
        keyword="sort_order",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=CANNOT_CREATE_INDEX_ERROR,
        valid_inputs={
            BsonType.DOUBLE: 1.0,
            BsonType.INT: 1,
            BsonType.LONG: Int64(1),
            BsonType.DECIMAL: Decimal128("1"),
        },
    ),
]


REJECTION_CASES = generate_bson_rejection_test_cases(SINGLE_KEY_SORT_ORDER_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_single_key_sort_order_rejected(collection, bson_type, sample_value, spec):
    """Test single field index creation rejects invalid BSON types for key sort order."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": sample_value}, "name": "test_idx"}],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(SINGLE_KEY_SORT_ORDER_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_single_key_sort_order_accepted(collection, bson_type, sample_value, spec):
    """Test single field index creation accepts valid BSON types for key sort order.

    Note: This is a type validation test, not a functional test. We only verify
    the command does not error — we do not check listIndexes to confirm the index
    was created with the correct option value.
    """
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": sample_value}, "name": "test_idx"}],
        },
    )
    assertNotError(result, msg=f"sort order should accept {bson_type.value}")
