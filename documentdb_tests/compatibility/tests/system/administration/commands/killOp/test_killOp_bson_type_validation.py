"""Tests for killOp BSON type validation."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq, NotExists
from documentdb_tests.framework.test_constants import NON_RUNNING_OP_ID

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


KILLOP_VALUE_PARAM = [
    BsonTypeTestCase(
        id="killOp_value",
        msg="killOp should accept all BSON types for the command field value",
        keyword="killOp",
        valid_types=list(BsonType),
        requires={"op": NON_RUNNING_OP_ID},
    ),
]

COMMENT_PARAM = [
    BsonTypeTestCase(
        id="comment",
        msg="killOp should accept all BSON types for the comment field",
        keyword="comment",
        valid_types=list(BsonType),
        requires={"op": NON_RUNNING_OP_ID},
    ),
]

OP_VALUE_PARAM = [
    BsonTypeTestCase(
        id="op",
        msg="op field should accept numeric types only",
        keyword="op",
        valid_types=[
            BsonType.INT,
            BsonType.DOUBLE,
            BsonType.LONG,
            BsonType.DECIMAL,
        ],
        valid_inputs={
            BsonType.DOUBLE: 999999.0,
            BsonType.LONG: Int64(999999),
            BsonType.DECIMAL: Decimal128("999999"),
        },
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

# killOp and comment accept all BSON types, so they have acceptance cases only (no rejections).
KILLOP_ACCEPTANCE = generate_bson_acceptance_test_cases(KILLOP_VALUE_PARAM)
COMMENT_ACCEPTANCE = generate_bson_acceptance_test_cases(COMMENT_PARAM)
OP_ACCEPTANCE = generate_bson_acceptance_test_cases(OP_VALUE_PARAM)
OP_REJECTIONS = generate_bson_rejection_test_cases(OP_VALUE_PARAM)


@pytest.mark.parametrize("bson_type,sample_value,spec", KILLOP_ACCEPTANCE)
def test_killOp_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test killOp accepts valid BSON types for the killOp command field."""
    result = execute_admin_command(collection, {"killOp": sample_value, "op": NON_RUNNING_OP_ID})
    assertProperties(
        result,
        {"ok": Eq(1.0)},
        msg=f"{spec.msg} (bson_type={bson_type.value})",
        raw_res=True,
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", COMMENT_ACCEPTANCE)
def test_killOp_comment_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test comment field accepts all BSON types and is consumed (not echoed back)."""
    result = execute_admin_command(
        collection, {"killOp": 1, "comment": sample_value, "op": NON_RUNNING_OP_ID}
    )
    assertProperties(
        result,
        {"ok": Eq(1.0), "comment": NotExists()},
        msg=f"{spec.msg} (bson_type={bson_type.value})",
        raw_res=True,
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", OP_ACCEPTANCE)
def test_killOp_op_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test op field accepts the numeric BSON types."""
    result = execute_admin_command(collection, {"killOp": 1, "op": sample_value})
    assertProperties(
        result,
        {"ok": Eq(1.0)},
        msg=f"{spec.msg} (bson_type={bson_type.value})",
        raw_res=True,
    )


@pytest.mark.parametrize("bson_type,sample_value,spec", OP_REJECTIONS)
def test_killOp_op_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test op field rejects non-numeric BSON types."""
    result = execute_admin_command(collection, {"killOp": 1, "op": sample_value})
    assertFailureCode(
        result,
        spec.expected_code(bson_type),
        msg=f"killOp should reject {bson_type.value} for op field",
    )
