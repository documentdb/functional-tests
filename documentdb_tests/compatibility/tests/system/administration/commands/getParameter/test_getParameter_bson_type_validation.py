"""Tests for getParameter BSON type validation."""

import pytest

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq, IsType, NotExists

pytestmark = pytest.mark.admin


GET_PARAMETER_VALUE_PARAMS = [
    BsonTypeTestCase(
        id="getParameter_value",
        msg="getParameter should accept all BSON types for the command field value",
        keyword="getParameter",
        valid_types=list(BsonType),
        valid_inputs={BsonType.OBJECT: {"showDetails": True}},
    ),
]

COMMENT_PARAMS = [
    BsonTypeTestCase(
        id="comment",
        msg="getParameter should accept all BSON types for the comment field",
        keyword="comment",
        valid_types=list(BsonType),
    ),
]

SET_AT_PARAMS = [
    BsonTypeTestCase(
        id="setAt",
        msg="setAt should accept string and null",
        keyword="setAt",
        valid_types=[BsonType.STRING, BsonType.NULL],
        requires={"allParameters": True},
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={BsonType.STRING: "runtime"},
    ),
]

BSON_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="showDetails",
        msg="showDetails should accept bool, numeric, and null",
        keyword="showDetails",
        valid_types=[
            BsonType.BOOL,
            BsonType.INT,
            BsonType.DOUBLE,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.NULL,
        ],
        requires={"logLevel": 1},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="allParameters",
        msg="allParameters should accept bool, numeric, and null",
        keyword="allParameters",
        valid_types=[
            BsonType.BOOL,
            BsonType.INT,
            BsonType.DOUBLE,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.NULL,
        ],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]


GET_PARAMETER_VALUE_ACCEPTANCE = generate_bson_acceptance_test_cases(GET_PARAMETER_VALUE_PARAMS)

COMMENT_ACCEPTANCE = generate_bson_acceptance_test_cases(COMMENT_PARAMS)

SETAT_ACCEPTANCE = generate_bson_acceptance_test_cases(SET_AT_PARAMS)

# GET_PARAMETER_VALUE_PARAMS and COMMENT_PARAMS accept all BSON types, so no rejections.
ALL_REJECTIONS = generate_bson_rejection_test_cases(SET_AT_PARAMS + BSON_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", GET_PARAMETER_VALUE_ACCEPTANCE)
def test_getParameter_value_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test getParameter command-field accepts all BSON types."""
    expected_type = "object" if isinstance(sample_value, dict) else "int"
    result = execute_admin_command(collection, {"getParameter": sample_value, "logLevel": 1})
    assertProperties(
        result,
        {"ok": Eq(1.0), "logLevel": IsType(expected_type)},
        msg=f"getParameter should accept {bson_type.value}",
        raw_res=True,
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", COMMENT_ACCEPTANCE)
def test_getParameter_comment_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test comment field accepts all BSON types."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "logLevel": 1, "comment": sample_value}
    )
    assertProperties(
        result,
        {"ok": Eq(1.0), "logLevel": IsType("int"), "comment": NotExists()},
        msg=f"comment should accept {bson_type.value}",
        raw_res=True,
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", SETAT_ACCEPTANCE)
def test_getParameter_setAt_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test setAt field accepts string and null."""
    result = execute_admin_command(
        collection, {"getParameter": {"allParameters": True, "setAt": sample_value}}
    )
    assertProperties(
        result, {"ok": Eq(1.0)}, msg=f"setAt should accept {bson_type.value}", raw_res=True
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", ALL_REJECTIONS)
def test_getParameter_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test document-form fields reject invalid BSON types."""
    from documentdb_tests.framework.assertions import assertFailureCode

    command = {"getParameter": {spec.keyword: sample_value}}
    if spec.requires:
        command["getParameter"].update(spec.requires)
        command.update({k: v for k, v in spec.requires.items() if k not in command["getParameter"]})
    result = execute_admin_command(collection, command)
    assertFailureCode(
        result, spec.default_error_code, msg=f"{spec.keyword} should reject {bson_type.value}"
    )
