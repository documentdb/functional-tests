"""Tests for bulkWrite bypassDocumentValidation value coercion and type rejection.

Mirrors ``aggregate/test_aggregate_bypass_validation.py``. bulkWrite-specific: a validator
failure surfaces as an op-level error (``nErrors:1``, ``cursor.firstBatch.0.code`` 121).
"""

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    DOCUMENT_VALIDATION_FAILURE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import CustomCollection
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_ZERO,
)

_VALIDATOR = {"$jsonSchema": {"bsonType": "object", "required": ["name"]}}


def _validated_collection() -> CustomCollection:
    return CustomCollection(options={"validator": _VALIDATOR})


_BYPASS = {"ok": Eq(1.0), "nErrors": Eq(0), "nInserted": Eq(1)}

BULKWRITE_BYPASS_TRUTHY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bypass_truthy_true",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": True,
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=true (truthy) should bypass the validator",
    ),
    CommandTestCase(
        "bypass_truthy_int32_1",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": 1,
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=int32 1 (truthy) should bypass the validator",
    ),
    CommandTestCase(
        "bypass_truthy_int64_1",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": Int64(1),
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=Int64 1 (truthy) should bypass the validator",
    ),
    CommandTestCase(
        "bypass_truthy_double_1",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": 1.0,
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=double 1.0 (truthy) should bypass the validator",
    ),
    CommandTestCase(
        "bypass_truthy_decimal128_1",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": Decimal128("1"),
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=Decimal128 1 (truthy) should bypass the validator",
    ),
    CommandTestCase(
        "bypass_truthy_nan",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": FLOAT_NAN,
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=NaN (truthy) should bypass the validator",
    ),
    CommandTestCase(
        "bypass_truthy_neg_nan",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": FLOAT_NEGATIVE_NAN,
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=-NaN (truthy) should bypass the validator",
    ),
    CommandTestCase(
        "bypass_truthy_decimal128_nan",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": DECIMAL128_NAN,
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=Decimal128 NaN (truthy) should bypass",
    ),
    CommandTestCase(
        "bypass_truthy_decimal128_neg_nan",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": DECIMAL128_NEGATIVE_NAN,
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=Decimal128 -NaN (truthy) should bypass",
    ),
    CommandTestCase(
        "bypass_truthy_infinity",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": FLOAT_INFINITY,
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=Infinity (truthy) should bypass the validator",
    ),
    CommandTestCase(
        "bypass_truthy_neg_infinity",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": FLOAT_NEGATIVE_INFINITY,
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=-Infinity (truthy) should bypass the validator",
    ),
    CommandTestCase(
        "bypass_truthy_decimal128_infinity",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": DECIMAL128_INFINITY,
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=Decimal128 Infinity (truthy) should bypass",
    ),
    CommandTestCase(
        "bypass_truthy_decimal128_neg_infinity",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": DECIMAL128_NEGATIVE_INFINITY,
        },
        expected=_BYPASS,
        msg="bulkWrite bypassDocumentValidation=Decimal128 -Infinity (truthy) should bypass",
    ),
]

_ENFORCE = {
    "ok": Eq(1.0),
    "nErrors": Eq(1),
    "nInserted": Eq(0),
    "cursor.firstBatch.0.ok": Eq(0.0),
    "cursor.firstBatch.0.idx": Eq(0),
    "cursor.firstBatch.0.code": Eq(DOCUMENT_VALIDATION_FAILURE_ERROR),
}

BULKWRITE_BYPASS_FALSY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bypass_falsy_false",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": False,
        },
        expected=_ENFORCE,
        msg="bulkWrite bypassDocumentValidation=false (falsy) should enforce the validator",
    ),
    CommandTestCase(
        "bypass_falsy_int32_0",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": INT32_ZERO,
        },
        expected=_ENFORCE,
        msg="bulkWrite bypassDocumentValidation=int32 0 (falsy) should enforce the validator",
    ),
    CommandTestCase(
        "bypass_falsy_double_0",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": DOUBLE_ZERO,
        },
        expected=_ENFORCE,
        msg="bulkWrite bypassDocumentValidation=double 0.0 (falsy) should enforce the validator",
    ),
    CommandTestCase(
        "bypass_falsy_double_neg_zero",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": DOUBLE_NEGATIVE_ZERO,
        },
        expected=_ENFORCE,
        msg="bulkWrite bypassDocumentValidation=double -0.0 (falsy) should enforce the validator",
    ),
    CommandTestCase(
        "bypass_falsy_decimal128_0",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": DECIMAL128_ZERO,
        },
        expected=_ENFORCE,
        msg="bulkWrite bypassDocumentValidation=Decimal128 0 (falsy) should enforce the validator",
    ),
    CommandTestCase(
        "bypass_falsy_decimal128_neg_zero",
        target_collection=_validated_collection(),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": DECIMAL128_NEGATIVE_ZERO,
        },
        expected=_ENFORCE,
        msg="bulkWrite bypassDocumentValidation=Decimal128 -0 (falsy) should enforce the validator",
    ),
]

_OPS = [{"insert": 0, "document": {"_id": 1}}]

BULKWRITE_BYPASS_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bypass_reject_string",
        command={"bulkWrite": 1, "ops": _OPS, "bypassDocumentValidation": "hello"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bulkWrite should reject string for bypassDocumentValidation with TypeMismatch",
    ),
    CommandTestCase(
        "bypass_reject_array",
        command={"bulkWrite": 1, "ops": _OPS, "bypassDocumentValidation": [1, 2]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bulkWrite should reject array for bypassDocumentValidation with TypeMismatch",
    ),
    CommandTestCase(
        "bypass_reject_document",
        command={"bulkWrite": 1, "ops": _OPS, "bypassDocumentValidation": {"a": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bulkWrite should reject document for bypassDocumentValidation with TypeMismatch",
    ),
    CommandTestCase(
        "bypass_reject_objectid",
        command={"bulkWrite": 1, "ops": _OPS, "bypassDocumentValidation": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bulkWrite should reject objectid for bypassDocumentValidation with TypeMismatch",
    ),
    CommandTestCase(
        "bypass_reject_datetime",
        command={
            "bulkWrite": 1,
            "ops": _OPS,
            "bypassDocumentValidation": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="bulkWrite should reject datetime for bypassDocumentValidation with TypeMismatch",
    ),
    CommandTestCase(
        "bypass_reject_timestamp",
        command={"bulkWrite": 1, "ops": _OPS, "bypassDocumentValidation": Timestamp(1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bulkWrite should reject timestamp for bypassDocumentValidation with TypeMismatch",
    ),
    CommandTestCase(
        "bypass_reject_regex",
        command={"bulkWrite": 1, "ops": _OPS, "bypassDocumentValidation": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bulkWrite should reject regex for bypassDocumentValidation with TypeMismatch",
    ),
    CommandTestCase(
        "bypass_reject_binary",
        command={"bulkWrite": 1, "ops": _OPS, "bypassDocumentValidation": Binary(b"hello")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bulkWrite should reject binary for bypassDocumentValidation with TypeMismatch",
    ),
    CommandTestCase(
        "bypass_reject_code",
        command={"bulkWrite": 1, "ops": _OPS, "bypassDocumentValidation": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bulkWrite should reject code for bypassDocumentValidation with TypeMismatch",
    ),
    CommandTestCase(
        "bypass_reject_code_with_scope",
        command={
            "bulkWrite": 1,
            "ops": _OPS,
            "bypassDocumentValidation": Code("function(){}", {"x": 1}),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="bulkWrite should reject code_with_scope for bypassDocumentValidation",
    ),
    CommandTestCase(
        "bypass_reject_minkey",
        command={"bulkWrite": 1, "ops": _OPS, "bypassDocumentValidation": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bulkWrite should reject minkey for bypassDocumentValidation with TypeMismatch",
    ),
    CommandTestCase(
        "bypass_reject_maxkey",
        command={"bulkWrite": 1, "ops": _OPS, "bypassDocumentValidation": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bulkWrite should reject maxkey for bypassDocumentValidation with TypeMismatch",
    ),
]

BULKWRITE_BYPASS_VALIDATION_TESTS = (
    BULKWRITE_BYPASS_TRUTHY_TESTS + BULKWRITE_BYPASS_FALSY_TESTS + BULKWRITE_BYPASS_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(BULKWRITE_BYPASS_VALIDATION_TESTS))
def test_bulkWrite_bypass_validation(database_client, collection, test):
    """Test bulkWrite bypassDocumentValidation value coercion and type rejection."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = test.build_command(ctx)
    if "nsInfo" not in command:
        command = {**command, "nsInfo": [{"ns": ctx.namespace}]}
    result = execute_admin_command(collection, command)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
