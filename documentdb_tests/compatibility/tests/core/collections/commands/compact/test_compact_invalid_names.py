"""Tests for compact command collection name validation errors."""

import uuid
from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_NAMESPACE_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Collection Name Type Errors]: non-string BSON types for the
# compact field produce an invalid namespace error.
COMPACT_COLLECTION_NAME_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_type_int32",
        command={"compact": 123},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="int32 collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_int64",
        command={"compact": Int64(1)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Int64 collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_double",
        command={"compact": 1.5},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="double collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_decimal128",
        command={"compact": Decimal128("1")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Decimal128 collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_bool",
        command={"compact": True},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="bool collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_null",
        command={"compact": None},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="null collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_array",
        command={"compact": ["a"]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="array collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_object",
        command={"compact": {"x": 1}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="object collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_objectid",
        command={"compact": ObjectId()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="ObjectId collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_datetime",
        command={"compact": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="datetime collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_timestamp",
        command={"compact": Timestamp(1, 1)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Timestamp collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_binary",
        command={"compact": Binary(b"hello")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Binary subtype 0 collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_binary_uuid",
        command={"compact": Binary(uuid.uuid4().bytes, 4)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Binary subtype 4 (UUID) should be rejected with UUID-specific message",
    ),
    CommandTestCase(
        "name_type_binary_user_defined",
        command={"compact": Binary(b"hello", 128)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Binary subtype 128 collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_regex",
        command={"compact": Regex(".*")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Regex collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_code",
        command={"compact": Code("x")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Code collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_code_with_scope",
        command={"compact": Code("x", {"a": 1})},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Code with scope collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_minkey",
        command={"compact": MinKey()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="MinKey collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_maxkey",
        command={"compact": MaxKey()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="MaxKey collection name should be rejected as invalid type",
    ),
]

# Property [Collection Name Validation Errors - Structural]: structurally
# invalid collection names produce an invalid namespace error.
COMPACT_COLLECTION_NAME_VALIDATION_STRUCTURAL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_empty_string",
        command={"compact": ""},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Empty string collection name should be rejected",
    ),
    CommandTestCase(
        "name_null_byte_embedded",
        command={"compact": "abc\x00def"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Null byte embedded in collection name should be rejected",
    ),
    CommandTestCase(
        "name_leading_dot",
        command={"compact": ".leading"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Leading dot in collection name should be rejected",
    ),
]

# Property [Collection Name Validation Errors - Not Found]: syntactically
# valid but non-existent or disallowed collection names produce a namespace
# not found error.
COMPACT_COLLECTION_NAME_NOT_FOUND_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_nonexistent",
        docs=None,
        command=lambda ctx: {"compact": ctx.collection},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Non-existent collection name should be rejected as not found",
    ),
    CommandTestCase(
        "name_dollar_prefix",
        command={"compact": "$test"},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Dollar-prefix name should be rejected as not found",
    ),
    CommandTestCase(
        "name_bare_dollar",
        command={"compact": "$"},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Bare dollar sign should be rejected as not found",
    ),
    CommandTestCase(
        "name_exceeds_namespace_limit",
        command={"compact": "a" * 256},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Name exceeding 255-byte namespace limit should be rejected as not found",
    ),
]

COMPACT_INVALID_NAME_TESTS: list[CommandTestCase] = (
    COMPACT_COLLECTION_NAME_TYPE_ERROR_TESTS
    + COMPACT_COLLECTION_NAME_VALIDATION_STRUCTURAL_TESTS
    + COMPACT_COLLECTION_NAME_NOT_FOUND_TESTS
)


@pytest.mark.requires(unforced_compact=True)
@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMPACT_INVALID_NAME_TESTS))
def test_compact_invalid_names(database_client, collection, test):
    """Test compact command rejects invalid collection names."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
