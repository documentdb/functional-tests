"""Tests for setParameter BSON type validation (success cases).

Validates control field acceptance of all BSON types, and type coercion
behavior for boolean and integer parameter values.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
)
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
        pytest.param(True, "bool True", id="true"),
        pytest.param(False, "bool False", id="false"),
        pytest.param(1, "int 1", id="int1"),
        pytest.param(0, "int 0", id="int0"),
        pytest.param(1.0, "double 1.0", id="double1"),
        pytest.param(0.0, "double 0.0", id="double0"),
        pytest.param(Int64(1), "Int64(1)", id="long1"),
        pytest.param(Int64(0), "Int64(0)", id="long0"),
        pytest.param("true", "string 'true'", id="string"),
        pytest.param([True], "array [True]", id="array"),
        pytest.param({"a": True}, "document", id="document"),
    ],
)
def test_setParameter_boolean_coercion_accepted(collection, value, desc):
    """Test setParameter boolean parameter coercion."""
    original = execute_admin_command(collection, {"getParameter": 1, "quiet": 1})
    result = execute_admin_command(collection, {"setParameter": 1, "quiet": value})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg=f"setParameter boolean param should accept {desc}"
    )
    execute_admin_command(collection, {"setParameter": 1, "quiet": original["quiet"]})


# Property [Integer Coercion Accepted]: integer-typed params accept whole-number numerics.
@pytest.mark.parametrize(
    "value,desc",
    [
        pytest.param(1, "int32", id="int32"),
        pytest.param(Int64(1), "Int64", id="long"),
        pytest.param(1.0, "whole double", id="whole_double"),
        pytest.param(Decimal128("1"), "Decimal128 whole", id="decimal128_whole"),
        pytest.param(True, "bool True", id="bool"),
    ],
)
def test_setParameter_integer_coercion_accepted(collection, value, desc):
    """Test setParameter integer parameter coercion."""
    result = execute_admin_command(collection, {"setParameter": 1, "logLevel": value})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg=f"setParameter integer param should accept {desc}"
    )
    execute_admin_command(collection, {"setParameter": 1, "logLevel": 0})
