"""
Insert bypassDocumentValidation tests.

Tests bypassDocumentValidation behavior with schema validation.
Collection names are derived from the fixture collection name to avoid
collisions under parallel execution.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    DOCUMENT_VALIDATION_FAILURE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection, TargetCollection
from documentdb_tests.framework.test_case import BaseTestCase

# Sentinel meaning the bypassDocumentValidation field is omitted from the command.
_OMIT = object()

_NAME_VALIDATOR = {
    "validator": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name"],
            "properties": {"name": {"bsonType": "string"}},
        }
    }
}


@dataclass(frozen=True)
class BypassTest(BaseTestCase):
    """Test case for bypassDocumentValidation semantics and numeric coercion."""

    bypass_value: Any = _OMIT
    document: Any = None
    target_collection: TargetCollection = TargetCollection()


# Property [bypassDocumentValidation Semantics]: controls whether schema validation
# is enforced. True or truthy numeric values skip validation; False, falsy numeric
# values, or omitting the field enforce it. The field has no effect on collections
# without a validator. String, array, and object values are rejected.
BYPASS_TESTS: list[BypassTest] = [
    # Core true/false/omit behavior on a validated collection
    BypassTest(
        "valid_doc_no_bypass",
        bypass_value=_OMIT,
        document={"_id": 1, "name": "Alice"},
        target_collection=CustomCollection(options=_NAME_VALIDATOR),
        expected={"ok": 1.0, "n": 1},
        msg="insert should succeed when document satisfies the validator.",
    ),
    BypassTest(
        "invalid_doc_no_bypass",
        bypass_value=_OMIT,
        document={"_id": 1, "value": 123},
        target_collection=CustomCollection(options=_NAME_VALIDATOR),
        expected={"writeErrors": [{"code": DOCUMENT_VALIDATION_FAILURE_ERROR}]},
        msg="insert should enforce validation when bypassDocumentValidation is omitted.",
    ),
    BypassTest(
        "invalid_doc_bypass_true",
        bypass_value=True,
        document={"_id": 1, "value": 123},
        target_collection=CustomCollection(options=_NAME_VALIDATOR),
        expected={"ok": 1.0, "n": 1},
        msg="insert should skip validation when bypassDocumentValidation is true.",
    ),
    BypassTest(
        "invalid_doc_bypass_false",
        bypass_value=False,
        document={"_id": 1, "value": 123},
        target_collection=CustomCollection(options=_NAME_VALIDATOR),
        expected={"writeErrors": [{"code": DOCUMENT_VALIDATION_FAILURE_ERROR}]},
        msg="insert should enforce validation when bypassDocumentValidation is false.",
    ),
    # No effect on a plain collection
    BypassTest(
        "bypass_no_validator",
        bypass_value=True,
        document={"_id": 1, "anything": "goes"},
        target_collection=TargetCollection(),
        expected={"ok": 1.0, "n": 1},
        msg="insert bypass on a collection without a validator should succeed.",
    ),
    # Numeric coercion — truthy values skip validation
    BypassTest(
        "bypass_int_one",
        bypass_value=1,
        document={"_id": 1, "value": 123},
        target_collection=CustomCollection(options=_NAME_VALIDATOR),
        expected={"ok": 1.0, "n": 1},
        msg="insert should treat bypassDocumentValidation=1 as truthy.",
    ),
    BypassTest(
        "bypass_double_one",
        bypass_value=1.0,
        document={"_id": 1, "value": 123},
        target_collection=CustomCollection(options=_NAME_VALIDATOR),
        expected={"ok": 1.0, "n": 1},
        msg="insert should treat bypassDocumentValidation=1.0 as truthy.",
    ),
    # Numeric coercion — falsy values enforce validation
    BypassTest(
        "bypass_int_zero",
        bypass_value=0,
        document={"_id": 1, "value": 123},
        target_collection=CustomCollection(options=_NAME_VALIDATOR),
        expected={"writeErrors": [{"code": DOCUMENT_VALIDATION_FAILURE_ERROR}]},
        msg="insert should treat bypassDocumentValidation=0 as falsy.",
    ),
    BypassTest(
        "bypass_double_zero",
        bypass_value=0.0,
        document={"_id": 1, "value": 123},
        target_collection=CustomCollection(options=_NAME_VALIDATOR),
        expected={"writeErrors": [{"code": DOCUMENT_VALIDATION_FAILURE_ERROR}]},
        msg="insert should treat bypassDocumentValidation=0.0 as falsy.",
    ),
    BypassTest(
        "bypass_null",
        bypass_value=None,
        document={"_id": 1, "value": 123},
        target_collection=CustomCollection(options=_NAME_VALIDATOR),
        expected={"writeErrors": [{"code": DOCUMENT_VALIDATION_FAILURE_ERROR}]},
        msg="insert should treat bypassDocumentValidation=null as falsy.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(BYPASS_TESTS))
def test_insert_bypass_validation(collection, test: BypassTest):
    """Test insert bypassDocumentValidation semantics and numeric coercion."""
    target = test.target_collection.resolve(collection.database, collection)
    try:
        cmd: dict[str, Any] = {
            "insert": target.name,
            "documents": [test.document],
        }
        if test.bypass_value is not _OMIT:
            cmd["bypassDocumentValidation"] = test.bypass_value
        result = execute_command(target, cmd)
        assertSuccessPartial(result, test.expected, msg=test.msg)
    finally:
        if target.name != collection.name:
            target.drop()


# Property [bypassDocumentValidation Type Rejection]: string, array, and object are not
# in the accepted type set [long, bool, double, int, decimal] and are rejected.
_BYPASS_REJECTED_PARAMS = [
    pytest.param("true", id="string_nonempty"),
    pytest.param("", id="string_empty"),
    pytest.param([], id="array"),
    pytest.param({}, id="object"),
]


@pytest.mark.insert
@pytest.mark.parametrize("bypass_value", _BYPASS_REJECTED_PARAMS)
def test_insert_bypass_rejects_invalid_type(collection, bypass_value):
    """Test bypassDocumentValidation rejects types outside [long, bool, double, int, decimal]."""
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": 1}],
            "bypassDocumentValidation": bypass_value,
        },
    )
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg="insert should reject invalid bypassDocumentValidation type.",
    )
