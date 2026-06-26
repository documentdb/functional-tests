"""Tests for setParameter BSON type validation.

Validates control field acceptance of all BSON types, and type coercion
behavior for boolean and integer parameter values.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [Control Field Acceptance]: setParameter control field accepts all BSON types.
CONTROL_FIELD_PARAM = [
    BsonTypeTestCase(
        id="setParameter_control",
        msg="setParameter control field should accept all BSON types",
        keyword="setParameter",
        valid_types=list(BsonType),
        requires={"logLevel": 0},
    ),
]

CONTROL_FIELD_ACCEPTANCE = generate_bson_acceptance_test_cases(CONTROL_FIELD_PARAM)


@pytest.mark.parametrize("bson_type,sample_value,spec", CONTROL_FIELD_ACCEPTANCE)
def test_setParameter_control_field_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test setParameter control field accepts all BSON types."""
    result = execute_admin_command(collection, {"setParameter": sample_value, "logLevel": 0})
    assertSuccessPartial(result, {"ok": 1.0}, msg=f"{spec.msg} (bson_type={bson_type.value})")


# Property [Boolean Coercion]: boolean-typed params accept many BSON types via coercion.
@pytest.mark.parametrize(
    "value,desc",
    [
        (True, "bool True"),
        (False, "bool False"),
        (1, "int 1"),
        (0, "int 0"),
        (1.0, "double 1.0"),
        (0.0, "double 0.0"),
        (Int64(1), "Int64(1)"),
        (Int64(0), "Int64(0)"),
        ("true", "string 'true'"),
        ([True], "array [True]"),
        ({"a": True}, "document"),
    ],
    ids=[
        "true",
        "false",
        "int1",
        "int0",
        "double1",
        "double0",
        "long1",
        "long0",
        "string",
        "array",
        "document",
    ],
)
def test_setParameter_boolean_coercion_accepted(collection, value, desc):
    """Test boolean parameter coercion — MongoDB 8.2 coerces many types to boolean."""
    original = execute_admin_command(collection, {"getParameter": 1, "quiet": 1})
    result = execute_admin_command(collection, {"setParameter": 1, "quiet": value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=f"Boolean param should accept {desc}")
    execute_admin_command(collection, {"setParameter": 1, "quiet": original["quiet"]})


# Property [Integer Coercion Accepted]: integer-typed params accept whole-number numerics.
@pytest.mark.parametrize(
    "value,desc",
    [
        (1, "int32"),
        (Int64(1), "Int64"),
        (1.0, "whole double"),
        (Decimal128("1"), "Decimal128 whole"),
        (True, "bool True"),
    ],
    ids=["int32", "long", "whole_double", "decimal128_whole", "bool"],
)
def test_setParameter_integer_coercion_accepted(collection, value, desc):
    """Test integer parameter coercion — whole-number numeric types and bool accepted."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=f"Integer param should accept {desc}")
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})


# Property [Integer Coercion Rejected]: integer-typed params reject non-numeric types.
@pytest.mark.parametrize(
    "value,error_code,desc",
    [
        ("1", BAD_VALUE_ERROR, "string '1'"),
        ([1], BAD_VALUE_ERROR, "array [1]"),
        ({"a": 1}, BAD_VALUE_ERROR, "document"),
    ],
    ids=["string", "array", "document"],
)
def test_setParameter_integer_coercion_rejected(collection, value, error_code, desc):
    """Test integer parameter rejects non-numeric types."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": value})
    assertFailureCode(result, error_code, msg=f"Integer param should reject {desc}")
