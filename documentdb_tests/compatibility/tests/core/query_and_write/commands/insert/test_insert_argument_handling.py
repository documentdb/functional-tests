"""Tests for insert command field type validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128, Int64, MaxKey, MinKey, Regex
from bson.binary import Binary

from documentdb_tests.framework.assertions import (
    assertExceptionType,
    assertResult,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_LENGTH_ERROR,
    INVALID_NAMESPACE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import DATE_EPOCH, INT64_MAX, OID_EPOCH, TS_EPOCH


@dataclass(frozen=True)
class FieldValidationTest(BaseTestCase):
    """Test case for insert command field validation errors."""

    command: Any = None


# Property [Command Field Rejection]: insert command rejects invalid BSON types for the
# collection name field, and rejects missing or empty documents array.
TESTS: list[FieldValidationTest] = [
    FieldValidationTest(
        "insert_field_rejects_int",
        command={"insert": 1, "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject integer type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_double",
        command={"insert": 3.14, "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject double type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_long",
        command={"insert": INT64_MAX, "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject long type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_bool",
        command={"insert": True, "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject boolean type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_null",
        command={"insert": None, "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject null type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_object",
        command={"insert": {"a": 1}, "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject object type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_array",
        command={"insert": [1, 2], "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject array type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_objectId",
        command={"insert": OID_EPOCH, "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject ObjectId type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_date",
        command={"insert": DATE_EPOCH, "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject date type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_regex",
        command={"insert": Regex(".*"), "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject regex type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_timestamp",
        command={"insert": TS_EPOCH, "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject timestamp type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_binary",
        command={"insert": Binary(b"\x01"), "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject binary type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_decimal128",
        command={"insert": Decimal128("1"), "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject Decimal128 type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_minKey",
        command={"insert": MinKey(), "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject MinKey type for collection name field.",
    ),
    FieldValidationTest(
        "insert_field_rejects_maxKey",
        command={"insert": MaxKey(), "documents": [{"_id": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject MaxKey type for collection name field.",
    ),
    FieldValidationTest(
        "empty_string_collection_name",
        command=None,  # Needs collection.name substitution
        error_code=INVALID_NAMESPACE_ERROR,
        msg="insert should reject empty string collection name.",
    ),
    FieldValidationTest(
        "empty_documents_array",
        command=None,
        error_code=INVALID_LENGTH_ERROR,
        msg="insert should reject empty documents array.",
    ),
    FieldValidationTest(
        "missing_documents_field",
        command=None,
        error_code=MISSING_FIELD_ERROR,
        msg="insert should reject missing documents field.",
    ),
    FieldValidationTest(
        "negative_maxtimems",
        command=None,
        error_code=BAD_VALUE_ERROR,
        msg="insert should reject negative maxTimeMS.",
    ),
]

_DYNAMIC_COMMANDS: dict[str, Any] = {
    "empty_string_collection_name": lambda n: {"insert": "", "documents": [{"_id": 1}]},
    "empty_documents_array": lambda n: {"insert": n, "documents": []},
    "missing_documents_field": lambda n: {"insert": n},
    "negative_maxtimems": lambda n: {"insert": n, "documents": [{"_id": 1}], "maxTimeMS": -1},
}


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_insert_field_validation(collection, test: FieldValidationTest):
    """Test insert command rejects invalid field types."""
    if test.command is not None:
        cmd = test.command
    else:
        cmd = _DYNAMIC_COMMANDS[test.id](collection.name)
    result = execute_command(collection, cmd)
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [Documents Element Rejection]: insert rejects non-document elements in the
# documents array (driver-side validation).
# Property [Documents Type Rejection]: insert rejects non-array types for the documents field.
# Both produce driver-side exceptions before reaching the server.
_DOCUMENTS_INVALID_TYPE_PARAMS = [
    pytest.param(1, id="int"),
    pytest.param(3.14, id="double"),
    pytest.param(True, id="bool"),
    pytest.param(None, id="null"),
    pytest.param({"a": 1}, id="object"),
    pytest.param("hello", id="string"),
    pytest.param(OID_EPOCH, id="objectId"),
    pytest.param(DATE_EPOCH, id="date"),
    pytest.param(Regex(".*"), id="regex"),
    pytest.param(TS_EPOCH, id="timestamp"),
    pytest.param(Binary(b"\x01"), id="binary"),
    pytest.param(Decimal128("1"), id="decimal128"),
    pytest.param(MinKey(), id="minKey"),
    pytest.param(MaxKey(), id="maxKey"),
]


@pytest.mark.insert
@pytest.mark.parametrize("docs_value", _DOCUMENTS_INVALID_TYPE_PARAMS)
def test_insert_documents_field_rejects_invalid_type(collection, docs_value):
    """Test that insert rejects non-array types for the documents field."""
    result = execute_command(collection, {"insert": collection.name, "documents": docs_value})
    assertExceptionType(result, Exception, msg="insert should reject non-array documents field.")


# Property [Documents Array Element Rejection]: insert rejects non-document elements in
# the documents array, including int, string, null, and array elements.
_DOCUMENTS_INVALID_ELEMENT_PARAMS = [
    pytest.param(1, id="int"),
    pytest.param("hello", id="string"),
    pytest.param(None, id="null"),
    pytest.param([1, 2], id="array"),
]


@pytest.mark.insert
@pytest.mark.parametrize("element", _DOCUMENTS_INVALID_ELEMENT_PARAMS)
def test_insert_documents_array_rejects_invalid_element(collection, element):
    """Test that insert rejects non-document elements in the documents array."""
    result = execute_command(collection, {"insert": collection.name, "documents": [element]})
    assertExceptionType(
        result, Exception, msg="insert should reject non-document element in documents array."
    )


# Property [Comment Acceptance]: insert accepts any BSON type for the comment field.
COMMENT_TYPES = [
    pytest.param("a comment", id="string"),
    pytest.param(42, id="int"),
    pytest.param(True, id="bool"),
    pytest.param(None, id="null"),
    pytest.param({"k": "v"}, id="object"),
    pytest.param([1, 2], id="array"),
]


@pytest.mark.insert
@pytest.mark.parametrize("comment", COMMENT_TYPES)
def test_insert_comment_accepts_any_type(collection, comment):
    """Test that comment field accepts any BSON type."""
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1}], "comment": comment},
    )
    assertSuccessPartial(result, {"ok": 1.0, "n": 1}, msg="insert should accept any comment type.")


# Property [Ordered Type Rejection]: insert rejects non-boolean-coercible types for ordered.
# null is accepted (treated as default). Numeric types and all non-bool non-null types
# produce TYPE_MISMATCH_ERROR.
_ORDERED_INVALID_PARAMS = [
    pytest.param({"ordered": "true"}, id="string"),
    pytest.param({"ordered": 1}, id="int"),
    pytest.param({"ordered": 1.0}, id="double"),
    pytest.param({"ordered": Int64(1)}, id="int64"),
    pytest.param({"ordered": Decimal128("1")}, id="decimal128"),
    pytest.param({"ordered": {"v": True}}, id="object"),
    pytest.param({"ordered": [True]}, id="array"),
    pytest.param({"ordered": DATE_EPOCH}, id="date"),
    pytest.param({"ordered": OID_EPOCH}, id="objectId"),
    pytest.param({"ordered": Regex(".*")}, id="regex"),
    pytest.param({"ordered": TS_EPOCH}, id="timestamp"),
    pytest.param({"ordered": Binary(b"\x01")}, id="binary"),
    pytest.param({"ordered": MinKey()}, id="minKey"),
    pytest.param({"ordered": MaxKey()}, id="maxKey"),
]


@pytest.mark.insert
@pytest.mark.parametrize("extra_fields", _ORDERED_INVALID_PARAMS)
def test_insert_ordered_rejects_invalid_type(collection, extra_fields):
    """Test insert rejects non-boolean ordered field."""
    cmd = {"insert": collection.name, "documents": [{"_id": 1}], **extra_fields}
    result = execute_command(collection, cmd)
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg="insert should reject non-boolean ordered field.",
    )


# Property [Unrecognized Field Rejection]: insert rejects unknown top-level command fields.
@pytest.mark.insert
def test_insert_rejects_unrecognized_field(collection):
    """Test insert rejects unrecognized top-level fields."""
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1}], "unknownField": 1},
    )
    assertResult(
        result,
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="insert should reject unrecognized fields.",
    )
