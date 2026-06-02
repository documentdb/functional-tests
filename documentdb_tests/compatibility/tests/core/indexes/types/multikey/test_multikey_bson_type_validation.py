"""Tests for multikey index key sort order BSON type validation.

Verifies that multikey index key values (sort order specifiers) reject
invalid BSON types and accept valid numeric types.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    index_created_response,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import CANNOT_CREATE_INDEX_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index

MULTIKEY_KEY_SORT_ORDER_PARAMS = [
    BsonTypeTestCase(
        id="sort_order",
        msg="multikey key sort order should reject non-numeric types",
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


REJECTION_CASES = generate_bson_rejection_test_cases(MULTIKEY_KEY_SORT_ORDER_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_multikey_key_sort_order_rejected(collection, bson_type, sample_value, spec):
    """Test multikey index creation rejects invalid BSON types for key sort order."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"arr": sample_value}, "name": "test_idx"}],
        },
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(MULTIKEY_KEY_SORT_ORDER_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_multikey_key_sort_order_accepted(collection, bson_type, sample_value, spec):
    """Test multikey index creation accepts valid BSON types for key sort order."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"arr": sample_value}, "name": "test_idx"}],
        },
    )
    assertSuccessPartial(
        result, index_created_response(), f"sort order should accept {bson_type.value}"
    )
